#!/usr/bin/env python3
"""Local-first visual puzzle transcription pipeline.

The script inventories evidence. It deliberately does not solve the puzzle.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    import cv2
    import numpy as np
except Exception as exc:  # pragma: no cover - environment guard
    raise SystemExit(f"OpenCV and NumPy are required in the selected Python: {exc}")


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


REVIEWED_STATUSES = {"已转录", "不确定"}


def read_image(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def write_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower() or ".png"
    ok, encoded = cv2.imencode(suffix, image)
    if not ok:
        raise ValueError(f"cannot encode image: {path}")
    encoded.tofile(str(path))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: serialize_csv(row.get(key, "")) for key in headers})


def serialize_csv(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return value


def order_quad(points: np.ndarray) -> np.ndarray:
    points = points.reshape(4, 2).astype(np.float32)
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).ravel()
    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(diffs)]
    ordered[3] = points[np.argmax(diffs)]
    return ordered


def perspective_correct(image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 180)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    area_total = image.shape[0] * image.shape[1]
    candidates: list[tuple[float, np.ndarray]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < area_total * 0.18:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            candidates.append((area, approx))
    if not candidates:
        return image.copy(), {"applied": False, "reason": "no_large_quadrilateral", "confidence": 0.0}
    area, quad = max(candidates, key=lambda item: item[0])
    src = order_quad(quad)
    tl, tr, br, bl = src
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if width < 80 or height < 80:
        return image.copy(), {"applied": False, "reason": "quadrilateral_too_small", "confidence": 0.0}
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    inverse_matrix = np.linalg.inv(matrix)
    warped = cv2.warpPerspective(image, matrix, (width, height), borderValue=(255, 255, 255))
    rectangularity = float(area / max(cv2.contourArea(cv2.convexHull(quad)), 1.0))
    coverage = float(area / area_total)
    return warped, {
        "applied": True,
        "corners": src.round(2).tolist(),
        "output_width": width,
        "output_height": height,
        "coverage": round(coverage, 4),
        "confidence": round(min(1.0, 0.55 * coverage + 0.45 * rectangularity), 4),
        "matrix": matrix.round(8).tolist(),
        "inverse_matrix": inverse_matrix.round(8).tolist(),
    }


def cluster_positions(indices: Iterable[int], tolerance: int) -> list[int]:
    groups: list[list[int]] = []
    for value in sorted(int(v) for v in indices):
        if not groups or value - groups[-1][-1] > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [int(round(sum(group) / len(group))) for group in groups]


def detect_grid(image: np.ndarray, rows: int | None, cols: int | None) -> dict[str, Any]:
    height, width = image.shape[:2]
    if rows and cols:
        x_lines = [int(round(i * width / cols)) for i in range(cols + 1)]
        y_lines = [int(round(i * height / rows)) for i in range(rows + 1)]
        x_lines[-1], y_lines[-1] = width - 1, height - 1
        return {"mode": "explicit", "x_lines": x_lines, "y_lines": y_lines, "rows": rows, "cols": cols, "confidence": 1.0}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 11)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, width // 18), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(12, height // 18)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    row_projection = (horizontal > 0).sum(axis=1)
    col_projection = (vertical > 0).sum(axis=0)
    y_candidates = np.where(row_projection >= max(20, width * 0.35))[0]
    x_candidates = np.where(col_projection >= max(20, height * 0.35))[0]
    x_lines = cluster_positions(x_candidates, max(2, width // 300))
    y_lines = cluster_positions(y_candidates, max(2, height // 300))
    x_lines = [x for x in x_lines if 0 <= x < width]
    y_lines = [y for y in y_lines if 0 <= y < height]

    valid = len(x_lines) >= 3 and len(y_lines) >= 3 and (len(x_lines) - 1) * (len(y_lines) - 1) <= 2500
    if valid:
        x_gaps = np.diff(x_lines)
        y_gaps = np.diff(y_lines)
        regular_x = 1.0 - min(1.0, float(np.std(x_gaps) / max(np.mean(x_gaps), 1.0)))
        regular_y = 1.0 - min(1.0, float(np.std(y_gaps) / max(np.mean(y_gaps), 1.0)))
        confidence = max(0.0, min(1.0, (regular_x + regular_y) / 2))
        return {
            "mode": "automatic",
            "x_lines": x_lines,
            "y_lines": y_lines,
            "rows": len(y_lines) - 1,
            "cols": len(x_lines) - 1,
            "confidence": round(confidence, 4),
        }

    return {
        "mode": "whole_image_fallback",
        "x_lines": [0, width - 1],
        "y_lines": [0, height - 1],
        "rows": 1,
        "cols": 1,
        "confidence": 0.0,
    }


def build_cells(image: np.ndarray, grid: dict[str, Any], cell_dir: Path) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    x_lines, y_lines = grid["x_lines"], grid["y_lines"]
    cell_dir.mkdir(parents=True, exist_ok=True)
    for row in range(len(y_lines) - 1):
        for col in range(len(x_lines) - 1):
            x1, x2 = x_lines[col], x_lines[col + 1]
            y1, y2 = y_lines[row], y_lines[row + 1]
            inset = max(1, min(x2 - x1, y2 - y1) // 40)
            crop = image[max(0, y1 + inset):max(y1 + inset + 1, y2 - inset), max(0, x1 + inset):max(x1 + inset + 1, x2 - inset)]
            region_id = f"R{row + 1:02d}C{col + 1:02d}"
            crop_path = cell_dir / f"{region_id}.png"
            write_image(crop_path, crop)
            cells.append({
                "region_id": region_id,
                "row": row + 1,
                "col": col + 1,
                "bbox": [int(x1), int(y1), int(max(1, x2 - x1)), int(max(1, y2 - y1))],
                "crop": str(crop_path),
            })
    return cells


def transform_region_points(points: np.ndarray, coordinate_space: str, perspective: dict[str, Any]) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    if coordinate_space == "normalized" or not perspective.get("applied"):
        return points
    matrix = np.asarray(perspective.get("matrix"), dtype=np.float32)
    if matrix.shape != (3, 3):
        raise ValueError("perspective matrix unavailable for input-space region manifest")
    return cv2.perspectiveTransform(points.reshape(1, -1, 2), matrix)[0]


def build_manifest_cells(
    image: np.ndarray,
    manifest_path: Path,
    image_sha256: str,
    perspective: dict[str, Any],
    cell_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read regions manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("regions manifest top level must be an object")
    if manifest.get("image_sha256") != image_sha256:
        raise ValueError("regions manifest image_sha256 does not match the input image")
    coordinate_space = manifest.get("coordinate_space", "input")
    if coordinate_space not in {"input", "normalized"}:
        raise ValueError("regions manifest coordinate_space must be input or normalized")
    regions = manifest.get("regions")
    if not isinstance(regions, list) or not regions:
        raise ValueError("regions manifest must contain a non-empty regions array")
    height, width = image.shape[:2]
    seen: set[str] = set()
    cells: list[dict[str, Any]] = []
    cell_dir.mkdir(parents=True, exist_ok=True)
    for index, region in enumerate(regions, 1):
        if not isinstance(region, dict):
            raise ValueError(f"region {index} must be an object")
        region_id = str(region.get("region_id", "")).strip()
        if not region_id or region_id in seen:
            raise ValueError(f"region {index} has an empty or duplicate region_id")
        seen.add(region_id)
        polygon_value = region.get("polygon")
        bbox_value = region.get("bbox")
        if polygon_value:
            polygon = transform_region_points(np.asarray(polygon_value, dtype=np.float32), coordinate_space, perspective)
        elif isinstance(bbox_value, list) and len(bbox_value) == 4:
            x, y, box_width, box_height = map(float, bbox_value)
            polygon = transform_region_points(
                np.asarray([[x, y], [x + box_width, y], [x + box_width, y + box_height], [x, y + box_height]], dtype=np.float32),
                coordinate_space,
                perspective,
            )
        else:
            raise ValueError(f"region {region_id} must contain polygon or bbox")
        x, y, box_width, box_height = cv2.boundingRect(np.rint(polygon).astype(np.int32))
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(width, x + box_width), min(height, y + box_height)
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"region {region_id} falls outside the normalized image")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", region_id).strip("_") or f"region_{index:04d}"
        crop_path = cell_dir / f"{safe_name}.png"
        write_image(crop_path, image[y1:y2, x1:x2])
        cells.append({
            "region_id": region_id,
            "row": int(region.get("row", index)),
            "col": int(region.get("col", 1)),
            "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
            "polygon": np.rint(polygon).astype(int).tolist(),
            "region_shape": "polygon",
            "region_kind": str(region.get("kind", "region")),
            "source_metadata": region.get("metadata", {}),
            "crop": str(crop_path),
        })
    rows = max((cell["row"] for cell in cells), default=len(cells))
    cols = max((cell["col"] for cell in cells), default=1)
    grid = {
        "mode": "external_region_manifest",
        "rows": rows,
        "cols": cols,
        "confidence": float((manifest.get("detector") or {}).get("confidence", 0.0)),
        "region_count": len(cells),
        "coordinate_space": coordinate_space,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "detector": manifest.get("detector", {}),
    }
    return cells, grid


def run_vision(image_path: Path, languages: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if sys.platform != "darwin" or not shutil.which("swift"):
        return [], {"engine": "vision-accurate", "success": False, "error": "macOS Swift/Vision unavailable"}
    cache_dir = Path("/private/tmp/vpt-swift-module-cache")
    binary = Path("/private/tmp/vpt-vision-ocr")
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        source = SCRIPT_DIR / "macos_vision_ocr.swift"
        if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
            compiler = shutil.which("swiftc")
            if not compiler:
                return [], {"engine": "vision-accurate", "success": False, "error": "swiftc unavailable"}
            compile_result = subprocess.run(
                [compiler, "-module-cache-path", str(cache_dir), "-o", str(binary), str(source)],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if compile_result.returncode != 0:
                return [], {"engine": "vision-accurate", "success": False, "error": compile_result.stderr.strip() or "Vision helper compile failed"}
        command = [str(binary), str(image_path), ",".join(languages), "accurate"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode != 0:
            return [], {"engine": "vision-accurate", "success": False, "error": result.stderr.strip() or f"exit {result.returncode}"}
        payload = json.loads(result.stdout)
        return payload.get("items", []), {"engine": payload.get("engine", "vision-accurate"), "success": True, "items": len(payload.get("items", []))}
    except Exception as exc:
        return [], {"engine": "vision-accurate", "success": False, "error": str(exc)}


def run_rapidocr(image_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()
        result, _elapsed = engine(str(image_path))
        items: list[dict[str, Any]] = []
        for record in result or []:
            box, text, score = record[0], record[1], float(record[2])
            points = np.asarray(box, dtype=float)
            x1, y1 = points[:, 0].min(), points[:, 1].min()
            x2, y2 = points[:, 0].max(), points[:, 1].max()
            items.append({
                "engine": "rapidocr",
                "text": str(text),
                "confidence": score,
                "bbox": [float(x1), float(y1), float(x2 - x1), float(y2 - y1)],
                "candidates": [{"text": str(text), "confidence": score}],
            })
        return items, {"engine": "rapidocr", "success": True, "items": len(items)}
    except Exception as exc:
        return [], {"engine": "rapidocr", "success": False, "error": str(exc)}


def run_tesseract(image_path: Path, languages: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    binary = shutil.which("tesseract")
    if not binary:
        return [], {"engine": "tesseract", "success": False, "error": "tesseract binary unavailable"}
    try:
        import pytesseract
        image = read_image(image_path)
        language_map = {"zh-Hans": "chi_sim", "zh-Hant": "chi_tra", "en-US": "eng", "en-GB": "eng"}
        lang = "+".join(dict.fromkeys(language_map.get(item, item) for item in languages))
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        items: list[dict[str, Any]] = []
        for i, text in enumerate(data.get("text", [])):
            text = str(text).strip()
            confidence = float(data["conf"][i]) if str(data["conf"][i]).strip() not in {"", "-1"} else -1
            if not text or confidence < 0:
                continue
            items.append({
                "engine": "tesseract",
                "text": text,
                "confidence": confidence / 100.0,
                "bbox": [float(data["left"][i]), float(data["top"][i]), float(data["width"][i]), float(data["height"][i])],
                "candidates": [{"text": text, "confidence": confidence / 100.0}],
            })
        return items, {"engine": "tesseract", "success": True, "items": len(items)}
    except Exception as exc:
        return [], {"engine": "tesseract", "success": False, "error": str(exc)}


def point_in_cell(x: float, y: float, cell: dict[str, Any]) -> bool:
    cx, cy, cw, ch = cell["bbox"]
    return cx <= x < cx + cw and cy <= y < cy + ch


def assign_ocr(cells: list[dict[str, Any]], engine_items: dict[str, list[dict[str, Any]]]) -> None:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {cell["region_id"]: defaultdict(list) for cell in cells}
    for engine, items in engine_items.items():
        for item in items:
            x, y, width, height = item["bbox"]
            center_x, center_y = x + width / 2, y + height / 2
            for cell in cells:
                if point_in_cell(center_x, center_y, cell):
                    grouped[cell["region_id"]][engine].append(item)
                    break
    for cell in cells:
        per_engine: dict[str, dict[str, Any]] = {}
        for engine, items in grouped[cell["region_id"]].items():
            ordered = sorted(items, key=lambda item: (item["bbox"][1], item["bbox"][0]))
            text = " ".join(item["text"].strip() for item in ordered if item["text"].strip())
            confidence = sum(float(item.get("confidence", 0.0)) for item in ordered) / max(len(ordered), 1)
            per_engine[engine] = {"text": text, "confidence": round(confidence, 4), "items": ordered}
        cell["ocr"] = per_engine
        fuse_ocr(cell)


def normalize_text(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE).casefold()


def fuse_ocr(cell: dict[str, Any]) -> None:
    readings = [(engine, data["text"], float(data["confidence"])) for engine, data in cell["ocr"].items() if data["text"].strip()]
    buckets: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for record in readings:
        buckets[normalize_text(record[1])].append(record)
    if not readings:
        cell.update({"text": "", "ocr_confidence": 0.0, "ocr_status": "无文本", "ocr_candidates": []})
        return
    best_key, best_group = max(buckets.items(), key=lambda item: (len(item[1]), sum(row[2] for row in item[1])))
    best = max(best_group, key=lambda row: row[2])
    agreement = len(best_group)
    candidate_rows = [
        {"engine": engine, "text": text, "confidence": round(score, 4), "normalized": normalize_text(text)}
        for engine, text, score in readings
    ]
    if agreement >= 2:
        status = "一致"
    elif len(readings) >= 2:
        status = "冲突"
    else:
        status = "单引擎"
    cell.update({
        "text": best[1],
        "ocr_confidence": round(sum(row[2] for row in best_group) / agreement, 4),
        "ocr_status": status,
        "ocr_candidates": candidate_rows,
        "ocr_agreement_count": agreement,
        "ocr_normalized": best_key,
    })


def color_clusters(crop: np.ndarray, count: int = 4) -> list[dict[str, Any]]:
    pixels = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).reshape(-1, 3)
    if len(pixels) > 12000:
        indices = np.linspace(0, len(pixels) - 1, 12000, dtype=int)
        pixels = pixels[indices]
    pixels_f = np.float32(pixels)
    unique_count = len(np.unique(pixels, axis=0))
    k = max(1, min(count, unique_count))
    cv2.setRNGSeed(42)
    _compactness, labels, centers = cv2.kmeans(
        pixels_f,
        k,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.3),
        4,
        cv2.KMEANS_PP_CENTERS,
    )
    totals = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(totals)[::-1]
    result = []
    for index in order:
        rgb = np.clip(np.rint(centers[index]), 0, 255).astype(int)
        result.append({
            "rgb": rgb.tolist(),
            "hex": "#" + "".join(f"{value:02X}" for value in rgb),
            "proportion": round(float(totals[index] / len(labels)), 4),
        })
    return result


def segment_intersection(a: list[int], b: list[int]) -> tuple[float, float] | None:
    x1, y1, x2, y2 = map(float, a)
    x3, y3, x4, y4 = map(float, b)
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-8:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
    tolerance = 4.0
    if (
        min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance
        and min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance
        and min(x3, x4) - tolerance <= px <= max(x3, x4) + tolerance
        and min(y3, y4) - tolerance <= py <= max(y3, y4) + tolerance
    ):
        return round(px, 2), round(py, 2)
    return None


def geometry_detect(image: np.ndarray) -> dict[str, Any]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 170)
    min_length = max(18, min(image.shape[:2]) // 18)
    raw_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=max(20, min_length // 2), minLineLength=min_length, maxLineGap=8)
    lines: list[dict[str, Any]] = []
    if raw_lines is not None:
        for index, values in enumerate(raw_lines[:300]):
            x1, y1, x2, y2 = map(int, values[0])
            angle = (math.degrees(math.atan2(y2 - y1, x2 - x1)) + 360) % 360
            lines.append({"id": f"L{index + 1:03d}", "points": [x1, y1, x2, y2], "angle": round(angle, 2), "length": round(math.hypot(x2 - x1, y2 - y1), 2)})

    intersections: list[dict[str, Any]] = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            angle_delta = abs(lines[i]["angle"] - lines[j]["angle"]) % 180
            angle_delta = min(angle_delta, 180 - angle_delta)
            if angle_delta < 12:
                continue
            point = segment_intersection(lines[i]["points"], lines[j]["points"])
            if point is not None:
                intersections.append({"id": f"X{len(intersections) + 1:03d}", "x": point[0], "y": point[1], "line_a": lines[i]["id"], "line_b": lines[j]["id"]})
            if len(intersections) >= 500:
                break
        if len(intersections) >= 500:
            break

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    triangles: list[tuple[float, float, float]] = []
    image_area = image.shape[0] * image.shape[1]
    for contour in contours:
        area = cv2.contourArea(contour)
        if not (8 <= area <= image_area * 0.015):
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if 3 <= len(approx) <= 5:
            moments = cv2.moments(contour)
            if moments["m00"]:
                triangles.append((moments["m10"] / moments["m00"], moments["m01"] / moments["m00"], area))

    arrows: list[dict[str, Any]] = []
    for line in lines:
        x1, y1, x2, y2 = line["points"]
        length = max(line["length"], 1.0)
        threshold = min(24.0, max(7.0, length * 0.22))
        matches = []
        for tx, ty, area in triangles:
            d1, d2 = math.hypot(tx - x1, ty - y1), math.hypot(tx - x2, ty - y2)
            if min(d1, d2) <= threshold:
                matches.append((min(d1, d2), tx, ty, "end" if d2 < d1 else "start", area))
        if not matches:
            continue
        _distance, tx, ty, endpoint, area = min(matches)
        if endpoint == "end":
            start, end = [x1, y1], [x2, y2]
        else:
            start, end = [x2, y2], [x1, y1]
        angle = (math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) + 360) % 360
        arrows.append({"id": f"A{len(arrows) + 1:03d}", "line_id": line["id"], "start": start, "end": end, "head_center": [round(tx, 2), round(ty, 2)], "direction_degrees": round(angle, 2), "head_area": round(area, 2), "method": "line_plus_polygon_heuristic"})

    # Second detector: identify an elongated filled contour with a sharp convex-hull tip.
    # This is particularly useful for colored arrows whose head and shaft form one contour.
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # High saturation isolates colored arrows from pale cell fills and black grid lines.
    # Dark arrows are still handled by the line-plus-polygon detector above.
    shape_mask = cv2.inRange(hsv, np.array([0, 120, 25]), np.array([179, 255, 245]))
    shape_mask = cv2.morphologyEx(shape_mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    shape_contours, _ = cv2.findContours(shape_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in shape_contours:
        area = cv2.contourArea(contour)
        if not (60 <= area <= image_area * 0.04):
            continue
        x, y, width, height = cv2.boundingRect(contour)
        aspect = max(width / max(height, 1), height / max(width, 1))
        if aspect < 1.45:
            continue
        raw_hull = cv2.convexHull(contour, returnPoints=True)
        hull = cv2.approxPolyDP(raw_hull, 0.025 * cv2.arcLength(raw_hull, True), True).reshape(-1, 2)
        if not (4 <= len(hull) <= 14):
            continue
        points = contour.reshape(-1, 2).astype(float)
        center_matrix, eigenvectors = cv2.PCACompute(points, np.empty((0)))
        center = center_matrix[0]
        axis = eigenvectors[0]
        centered = points - center
        parallel = centered @ axis
        perpendicular = centered @ np.array([-axis[1], axis[0]])
        low, high = float(parallel.min()), float(parallel.max())
        span = high - low
        if span <= 1:
            continue
        low_band = perpendicular[parallel <= low + span * 0.32]
        high_band = perpendicular[parallel >= high - span * 0.32]
        low_width = float(np.ptp(low_band)) if len(low_band) else 0.0
        high_width = float(np.ptp(high_band)) if len(high_band) else 0.0
        # The arrowhead end widens sharply before converging at the tip.
        head_at_high = high_width > low_width
        best_tip = points[np.argmax(parallel) if head_at_high else np.argmin(parallel)]
        if max(low_width, high_width) < min(width, height) * 0.22:
            continue
        direction = (math.degrees(math.atan2(float(best_tip[1] - center[1]), float(best_tip[0] - center[0]))) + 360) % 360
        duplicate = any(math.hypot(existing["head_center"][0] - best_tip[0], existing["head_center"][1] - best_tip[1]) < 18 for existing in arrows)
        if duplicate:
            continue
        arrows.append({
            "id": f"A{len(arrows) + 1:03d}",
            "line_id": "",
            "start": [int(round(center[0])), int(round(center[1]))],
            "end": [int(best_tip[0]), int(best_tip[1])],
            "head_center": [float(best_tip[0]), float(best_tip[1])],
            "direction_degrees": round(direction, 2),
            "head_area": round(area, 2),
            "method": "pca_head_width_heuristic",
        })
    return {"lines": lines, "intersections": intersections, "arrows": arrows, "edge_image": edges}


def associate_geometry(cells: list[dict[str, Any]], geometry: dict[str, Any]) -> None:
    for cell in cells:
        cell["line_ids"], cell["arrow_ids"], cell["intersection_ids"] = [], [], []
    for line in geometry["lines"]:
        x1, y1, x2, y2 = line["points"]
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        for cell in cells:
            if point_in_cell(*center, cell):
                cell["line_ids"].append(line["id"])
                line["region_id"] = cell["region_id"]
                break
    for arrow in geometry["arrows"]:
        center = arrow["head_center"]
        for cell in cells:
            if point_in_cell(center[0], center[1], cell):
                cell["arrow_ids"].append(arrow["id"])
                arrow["region_id"] = cell["region_id"]
                break
    for intersection in geometry["intersections"]:
        for cell in cells:
            if point_in_cell(intersection["x"], intersection["y"], cell):
                cell["intersection_ids"].append(intersection["id"])
                intersection["region_id"] = cell["region_id"]
                break


def analyze_cells(image: np.ndarray, cells: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    colors: list[dict[str, Any]] = []
    uncertain: list[dict[str, Any]] = []
    gray_full = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    for cell in cells:
        x, y, width, height = cell["bbox"]
        crop = image[y:y + height, x:x + width]
        gray = gray_full[y:y + height, x:x + width]
        clusters = color_clusters(crop)
        cell["colors"] = clusters
        for rank, cluster in enumerate(clusters, 1):
            colors.append({"region_id": cell["region_id"], "rank": rank, **cluster})
        edge_density = float((cv2.Canny(gray, 60, 170) > 0).mean()) if gray.size else 0.0
        std = float(gray.std()) if gray.size else 0.0
        cell["edge_density"] = round(edge_density, 4)
        cell["luminance_std"] = round(std, 2)
        blank_confirmed = std < 7.0 and edge_density < 0.012
        cell["blank_confirmed"] = blank_confirmed

        reason = ""
        if cell["ocr_status"] == "一致":
            status, confidence = "已转录", "高"
        elif cell["ocr_status"] == "冲突":
            status, confidence, reason = "不确定", "低", "OCR引擎读法冲突"
        elif cell["ocr_status"] == "单引擎":
            status, confidence, reason = "不确定", "中", "只有一个OCR引擎给出读法"
        elif blank_confirmed:
            status, confidence = "已转录", "高"
            cell["text"] = "[空白]"
        elif cell["line_ids"] or cell["arrow_ids"] or cell["intersection_ids"]:
            status, confidence, reason = "不确定", "中", "检测到几何元素，需人工确认含义"
        else:
            status, confidence, reason = "不确定", "低", "存在视觉内容但没有可靠文字或几何分类"
        cell["transcription_status"] = status
        cell["auto_transcription_status"] = status
        cell["confidence"] = confidence
        cell["review_note"] = reason
        cell["user_confirmed"] = "待确认"
        if status == "不确定":
            uncertain.append({
                "region_id": cell["region_id"],
                "bbox": cell["bbox"],
                "best_reading": cell.get("text", ""),
                "candidates": cell.get("ocr_candidates", []),
                "reason": reason,
                "crop": cell["crop"],
                "user_resolution": "",
            })
    return colors, uncertain


def make_review_template(image_sha256: str, cells: list[dict[str, Any]], grid: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "image_sha256": image_sha256,
        "inventory_verified": False,
        "reviewed_by": "",
        "reviewed_at": "",
        "grid_review": {
            "detected_mode": grid.get("mode", ""),
            "detected_rows": grid.get("rows", 0),
            "detected_cols": grid.get("cols", 0),
            "accepted": False,
            "notes": "检查是否漏掉整块面板、图例、边缘区域、斜格或非矩形区域。",
        },
        "expected_regions": [
            {
                "region_id": cell["region_id"],
                "bbox": cell["bbox"],
                "kind": "cell",
                "review_status": "未处理",
                "resolved_text": "",
                "notes": "",
            }
            for cell in cells
        ],
        "untracked_regions": [],
        "instructions": [
            "不要删除自动检测到的区域；如属误检，在 notes 中说明。",
            "把漏掉的面板、图例或格子加入 expected_regions；没有对应裁剪的区域会阻断锁定。",
            "逐项检查后把 review_status 改为 已转录 或 不确定。",
            "完整核对后填写 reviewed_by、reviewed_at，并把 grid_review.accepted 与 inventory_verified 设为 true。",
        ],
    }


def load_review_manifest(path: Path, image_sha256: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"审核清单无法读取: {exc}"]
    if not isinstance(manifest, dict):
        return None, ["审核清单顶层必须是对象"]
    if manifest.get("image_sha256") != image_sha256:
        errors.append("审核清单的图像SHA-256与本次输入不匹配")
    regions = manifest.get("expected_regions")
    if not isinstance(regions, list) or not regions:
        errors.append("审核清单没有 expected_regions")
        regions = []
    seen: set[str] = set()
    valid_statuses = {"未处理"} | REVIEWED_STATUSES
    for index, item in enumerate(regions, 1):
        if not isinstance(item, dict):
            errors.append(f"expected_regions 第 {index} 项不是对象")
            continue
        region_id = str(item.get("region_id", "")).strip()
        if not region_id:
            errors.append(f"expected_regions 第 {index} 项缺少 region_id")
        elif region_id in seen:
            errors.append(f"expected_regions 存在重复ID: {region_id}")
        seen.add(region_id)
        if item.get("review_status", "未处理") not in valid_statuses:
            errors.append(f"{region_id or index} 的 review_status 无效")
    if manifest.get("inventory_verified"):
        if not str(manifest.get("reviewed_by", "")).strip():
            errors.append("inventory_verified=true 但 reviewed_by 为空")
        if not str(manifest.get("reviewed_at", "")).strip():
            errors.append("inventory_verified=true 但 reviewed_at 为空")
        if not (manifest.get("grid_review") or {}).get("accepted"):
            errors.append("inventory_verified=true 但 grid_review.accepted 不是 true")
    return manifest, errors


def apply_review_manifest(
    cells: list[dict[str, Any]],
    uncertain: list[dict[str, Any]],
    manifest: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if not manifest or errors:
        return
    reviews = {
        str(item.get("region_id")): item
        for item in manifest.get("expected_regions", [])
        if isinstance(item, dict) and item.get("region_id")
    }
    uncertainty_by_id = {item["region_id"]: item for item in uncertain}
    for cell in cells:
        review = reviews.get(cell["region_id"])
        if review is None:
            cell["transcription_status"] = "未处理"
            cell["user_confirmed"] = "否"
            cell["review_note"] = "自动检测区域未列入人工审核清单"
            continue
        status = review.get("review_status", "未处理")
        cell["transcription_status"] = status
        cell["reviewed_text"] = str(review.get("resolved_text", ""))
        cell["effective_text"] = cell["reviewed_text"] or cell.get("text", "")
        cell["user_confirmed"] = "是" if status in REVIEWED_STATUSES else "待确认"
        notes = str(review.get("notes", "")).strip()
        if notes:
            cell["review_note"] = notes
        if cell["region_id"] in uncertainty_by_id:
            uncertainty_by_id[cell["region_id"]]["user_resolution"] = cell["reviewed_text"]


def align_and_diff(before: np.ndarray, after: np.ndarray, output_dir: Path) -> dict[str, Any]:
    if after.shape[:2] != before.shape[:2]:
        after = cv2.resize(after, (before.shape[1], before.shape[0]), interpolation=cv2.INTER_AREA)
    gray_before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    gray_after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    method = "resize_only"
    aligned = after
    try:
        orb = cv2.ORB_create(2500)
        kp1, des1 = orb.detectAndCompute(gray_before, None)
        kp2, des2 = orb.detectAndCompute(gray_after, None)
        if des1 is not None and des2 is not None:
            matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(des1, des2)
            matches = sorted(matches, key=lambda item: item.distance)[:250]
            if len(matches) >= 12:
                source = np.float32([kp2[item.trainIdx].pt for item in matches]).reshape(-1, 1, 2)
                target = np.float32([kp1[item.queryIdx].pt for item in matches]).reshape(-1, 1, 2)
                homography, mask = cv2.findHomography(source, target, cv2.RANSAC, 4.0)
                if homography is not None and mask is not None and int(mask.sum()) >= 8:
                    aligned = cv2.warpPerspective(after, homography, (before.shape[1], before.shape[0]))
                    method = "orb_homography"
    except cv2.error:
        pass
    diff = cv2.absdiff(before, aligned)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _threshold, mask = cv2.threshold(diff_gray, 25, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=2)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    components: list[dict[str, Any]] = []
    overlay = before.copy()
    min_area = max(12, int(before.shape[0] * before.shape[1] * 0.00008))
    for index in range(1, count):
        x, y, width, height, area = map(int, stats[index])
        if area < min_area:
            continue
        component = {"id": f"D{len(components) + 1:03d}", "bbox": [x, y, width, height], "area": area, "centroid": [round(float(centroids[index][0]), 2), round(float(centroids[index][1]), 2)]}
        components.append(component)
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (0, 0, 255), 2)
        cv2.putText(overlay, component["id"], (x, max(14, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 1, cv2.LINE_AA)
    write_image(output_dir / "after_aligned.png", aligned)
    write_image(output_dir / "diff_mask.png", mask)
    write_image(output_dir / "diff_overlay.png", overlay)
    return {"provided": True, "alignment": method, "changed_pixel_ratio": round(float((mask > 0).mean()), 6), "components": components}


def annotate(image: np.ndarray, cells: list[dict[str, Any]], geometry: dict[str, Any]) -> np.ndarray:
    canvas = image.copy()
    for cell in cells:
        x, y, width, height = cell["bbox"]
        color = (38, 139, 78) if cell["transcription_status"] == "已转录" else (0, 140, 255)
        cv2.rectangle(canvas, (x, y), (x + width, y + height), color, 2)
        cv2.rectangle(canvas, (x, y), (x + 76, y + 19), color, -1)
        cv2.putText(canvas, cell["region_id"], (x + 3, y + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (255, 255, 255), 1, cv2.LINE_AA)
    for arrow in geometry["arrows"]:
        cv2.arrowedLine(canvas, tuple(arrow["start"]), tuple(arrow["end"]), (255, 0, 180), 2, tipLength=0.25)
    for intersection in geometry["intersections"][:150]:
        cv2.circle(canvas, (int(round(intersection["x"])), int(round(intersection["y"]))), 3, (255, 80, 0), -1)
    return canvas


def associate_diff(cells: list[dict[str, Any]], difference: dict[str, Any]) -> None:
    for component in difference.get("components", []):
        center = component["centroid"]
        component["region_id"] = ""
        for cell in cells:
            if point_in_cell(center[0], center[1], cell):
                component["region_id"] = cell["region_id"]
                break


def build_gate(
    cells: list[dict[str, Any]],
    grid: dict[str, Any],
    engine_status: list[dict[str, Any]],
    threshold: float,
    review_manifest: dict[str, Any] | None,
    review_errors: list[str],
) -> dict[str, Any]:
    detected_ids = {cell["region_id"] for cell in cells}
    expected_items = review_manifest.get("expected_regions", []) if review_manifest else []
    expected_ids = {
        str(item.get("region_id"))
        for item in expected_items
        if isinstance(item, dict) and item.get("region_id")
    }
    if review_manifest:
        expected = len(expected_ids)
        reviewed_ids = {
            str(item.get("region_id"))
            for item in expected_items
            if isinstance(item, dict) and item.get("review_status") in REVIEWED_STATUSES
        }
        covered_ids = expected_ids & detected_ids & reviewed_ids
        missing_ids = expected_ids - detected_ids
        unreviewed_detected_ids = detected_ids - expected_ids
        declared_untracked = review_manifest.get("untracked_regions", [])
        declared_untracked_count = len(declared_untracked) if isinstance(declared_untracked, list) else 1
        covered = len(covered_ids)
        coverage = covered / expected if expected else 0.0
    else:
        expected = len(cells)
        covered = 0
        coverage = 0.0
        covered_ids = set()
        missing_ids = set()
        unreviewed_detected_ids = detected_ids
        declared_untracked_count = 0
    untracked = len(missing_ids) + len(unreviewed_detected_ids) + declared_untracked_count
    inventory_verified = bool(
        review_manifest
        and review_manifest.get("inventory_verified")
        and (review_manifest.get("grid_review") or {}).get("accepted")
        and not review_errors
    )
    successful_engines = [
        entry["engine"]
        for entry in engine_status
        if entry.get("success") and int(entry.get("items", 0) or 0) > 0
    ]
    text_present = any(cell.get("text") not in {"", "[空白]"} for cell in cells) or any(
        isinstance(item, dict) and item.get("kind") == "text" for item in expected_items
    )
    reasons: list[str] = []
    if not review_manifest:
        reasons.append("尚未导入独立人工审核清单；自动切格不能作为覆盖率分母")
    reasons.extend(review_errors)
    if coverage < threshold:
        reasons.append(f"转录覆盖率 {coverage:.1%} 低于阈值 {threshold:.1%}")
    if not inventory_verified:
        reasons.append("图像清单尚未由操作人确认")
    if grid["mode"] == "whole_image_fallback" and not inventory_verified:
        reasons.append("自动切格失败，目前只有整图回退区域且尚未完成人工审核")
    if untracked:
        reasons.append(f"仍有 {untracked} 个未跟踪或未纳入审核的区域")
    if text_present and len(successful_engines) < 2:
        reasons.append("文字材料少于两个实际产出结果的OCR引擎")
    return {
        "coverage_threshold": threshold,
        "expected_regions": expected,
        "covered_regions": covered,
        "coverage": round(coverage, 6),
        "inventory_verified": inventory_verified,
        "review_manifest_present": bool(review_manifest),
        "review_manifest_valid": bool(review_manifest) and not review_errors,
        "review_errors": review_errors,
        "untracked_regions": untracked,
        "covered_region_ids": sorted(covered_ids),
        "missing_region_ids": sorted(missing_ids),
        "unreviewed_detected_ids": sorted(unreviewed_detected_ids),
        "text_present": text_present,
        "successful_ocr_engines": successful_engines,
        "permission": "允许" if not reasons else "禁止",
        "blocking_reasons": reasons,
    }


def find_node_modules() -> Path | None:
    candidates = [
        SKILL_DIR / "node_modules",
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
    ]
    for candidate in candidates:
        if (candidate / "@oai" / "artifact-tool").exists():
            return candidate
    return None


def build_workbook(report_path: Path, output_dir: Path) -> dict[str, Any]:
    bundled_node = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    node = str(bundled_node) if bundled_node.exists() else shutil.which("node")
    node_modules = find_node_modules()
    if not node:
        return {"success": False, "error": "node executable unavailable"}
    if not node_modules:
        return {"success": False, "error": "@oai/artifact-tool dependency unavailable"}
    link = SKILL_DIR / "node_modules"
    if not link.exists():
        try:
            link.symlink_to(node_modules, target_is_directory=True)
        except OSError as exc:
            return {"success": False, "error": f"cannot create node_modules symlink: {exc}"}
    workbook_path = output_dir / "visual_transcription.xlsx"
    command = [node, str(SCRIPT_DIR / "build_transcription_workbook.mjs"), str(report_path), str(workbook_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    if result.returncode != 0:
        return {"success": False, "error": (result.stderr or result.stdout).strip()}
    return {"success": True, "path": str(workbook_path), "message": result.stdout.strip()}


def flatten_cell(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "region_id": cell["region_id"],
        "row": cell["row"],
        "col": cell["col"],
        "bbox": cell["bbox"],
        "crop": cell["crop"],
        "transcription_status": cell["transcription_status"],
        "auto_transcription_status": cell.get("auto_transcription_status", ""),
        "text": cell.get("text", ""),
        "reviewed_text": cell.get("reviewed_text", ""),
        "effective_text": cell.get("effective_text", cell.get("text", "")),
        "ocr_status": cell.get("ocr_status", ""),
        "ocr_confidence": cell.get("ocr_confidence", 0.0),
        "ocr_candidates": cell.get("ocr_candidates", []),
        "dominant_color": cell.get("colors", [{}])[0].get("hex", ""),
        "color_clusters": cell.get("colors", []),
        "line_ids": cell.get("line_ids", []),
        "arrow_ids": cell.get("arrow_ids", []),
        "intersection_ids": cell.get("intersection_ids", []),
        "confidence": cell.get("confidence", ""),
        "review_note": cell.get("review_note", ""),
        "user_confirmed": cell.get("user_confirmed", "待确认"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe visual puzzle evidence before solving.")
    parser.add_argument("image", type=Path, help="before-state or single puzzle image")
    parser.add_argument("--after", type=Path, help="optional after-click image")
    parser.add_argument("--output", type=Path, required=True, help="output directory")
    parser.add_argument("--rows", type=int, help="known grid rows")
    parser.add_argument("--cols", type=int, help="known grid columns")
    parser.add_argument("--regions-manifest", type=Path, help="external detector output using the generic region manifest schema")
    parser.add_argument("--coverage-threshold", type=float, default=0.95)
    parser.add_argument("--review-manifest", type=Path, help="reviewed inventory JSON generated by a prior run")
    parser.add_argument("--inventory-verified", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-perspective", action="store_true")
    parser.add_argument("--languages", default="zh-Hans,en-US")
    parser.add_argument("--ocr-engines", default="vision,rapidocr,tesseract")
    parser.add_argument("--no-workbook", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.rows) != bool(args.cols):
        raise SystemExit("--rows and --cols must be supplied together")
    if not 0 < args.coverage_threshold <= 1:
        raise SystemExit("coverage threshold must be in (0, 1]")
    if args.inventory_verified:
        raise SystemExit("--inventory-verified 已停用；请先运行生成 inventory_review_template.json，审核后用 --review-manifest 导入")
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.image.resolve()
    image_sha256 = sha256_file(input_path)
    image = read_image(input_path)
    original_path = output_dir / "original.png"
    write_image(original_path, image)

    if args.no_perspective:
        normalized = image.copy()
        perspective = {"applied": False, "reason": "disabled", "confidence": 0.0}
    else:
        normalized, perspective = perspective_correct(image)
    normalized_path = output_dir / "normalized.png"
    write_image(normalized_path, normalized)

    if args.regions_manifest:
        try:
            cells, grid = build_manifest_cells(
                normalized,
                args.regions_manifest.resolve(),
                image_sha256,
                perspective,
                output_dir / "cells",
            )
        except ValueError as exc:
            raise SystemExit(f"invalid --regions-manifest: {exc}") from exc
    else:
        grid = detect_grid(normalized, args.rows, args.cols)
        cells = build_cells(normalized, grid, output_dir / "cells")

    languages = [item.strip() for item in args.languages.split(",") if item.strip()]
    requested_engines = [item.strip().lower() for item in args.ocr_engines.split(",") if item.strip()]
    engine_items: dict[str, list[dict[str, Any]]] = {}
    engine_status: list[dict[str, Any]] = []
    adapters = {"vision": lambda: run_vision(normalized_path, languages), "rapidocr": lambda: run_rapidocr(normalized_path), "tesseract": lambda: run_tesseract(normalized_path, languages)}
    for engine in requested_engines:
        if engine not in adapters:
            engine_status.append({"engine": engine, "success": False, "error": "unknown OCR engine"})
            continue
        items, status = adapters[engine]()
        engine_items[status["engine"]] = items
        engine_status.append(status)
    assign_ocr(cells, engine_items)

    geometry = geometry_detect(normalized)
    write_image(output_dir / "geometry_edges.png", geometry.pop("edge_image"))
    associate_geometry(cells, geometry)
    colors, uncertain = analyze_cells(normalized, cells)
    review_manifest: dict[str, Any] | None = None
    review_errors: list[str] = []
    if args.review_manifest:
        review_manifest, review_errors = load_review_manifest(args.review_manifest.resolve(), image_sha256)
        apply_review_manifest(cells, uncertain, review_manifest, review_errors)
        if review_manifest:
            write_json(output_dir / "inventory_review_applied.json", review_manifest)
    else:
        write_json(output_dir / "inventory_review_template.json", make_review_template(image_sha256, cells, grid))

    if args.after:
        after = read_image(args.after.resolve())
        if perspective.get("applied"):
            after, _after_perspective = perspective_correct(after)
            if after.shape[:2] != normalized.shape[:2]:
                after = cv2.resize(after, (normalized.shape[1], normalized.shape[0]), interpolation=cv2.INTER_AREA)
        difference = align_and_diff(normalized, after, output_dir)
        associate_diff(cells, difference)
    else:
        difference = {"provided": False, "alignment": "not_applicable", "components": []}

    annotated = annotate(normalized, cells, geometry)
    write_image(output_dir / "annotated_regions.png", annotated)
    gate = build_gate(cells, grid, engine_status, args.coverage_threshold, review_manifest, review_errors)

    report = {
        "schema_version": "1.0",
        "input": {
            "image": str(input_path),
            "after": str(args.after.resolve()) if args.after else None,
            "image_id": f"sha256:{image_sha256}",
            "image_sha256": image_sha256,
            "after_sha256": sha256_file(args.after.resolve()) if args.after else None,
            "pipeline_sha256": sha256_file(Path(__file__).resolve()),
            "width": int(image.shape[1]),
            "height": int(image.shape[0]),
            "normalized_width": int(normalized.shape[1]),
            "normalized_height": int(normalized.shape[0]),
        },
        "perspective": perspective,
        "grid": grid,
        "engines": engine_status,
        "cells": [flatten_cell(cell) for cell in cells],
        "uncertain": uncertain,
        "colors": colors,
        "geometry": geometry,
        "difference": difference,
        "gate": gate,
        "review": {
            "manifest": str(args.review_manifest.resolve()) if args.review_manifest else None,
            "errors": review_errors,
        },
    }
    report_path = output_dir / "report.json"
    write_json(report_path, report)
    write_csv(output_dir / "逐格转录.csv", report["cells"], [
        "region_id", "row", "col", "bbox", "crop", "transcription_status", "auto_transcription_status", "text", "reviewed_text", "effective_text", "ocr_status", "ocr_confidence", "ocr_candidates", "dominant_color", "color_clusters", "line_ids", "arrow_ids", "intersection_ids", "confidence", "review_note", "user_confirmed",
    ])
    write_csv(output_dir / "不确定字符.csv", uncertain, ["region_id", "bbox", "best_reading", "candidates", "reason", "crop", "user_resolution"])
    write_csv(output_dir / "颜色聚类.csv", colors, ["region_id", "rank", "rgb", "hex", "proportion"])
    geometry_rows = []
    for kind in ("lines", "arrows", "intersections"):
        for record in geometry[kind]:
            geometry_rows.append({"kind": kind[:-1], **record})
    write_csv(output_dir / "几何元素.csv", geometry_rows, ["kind", "id", "region_id", "points", "angle", "length", "line_id", "start", "end", "head_center", "direction_degrees", "x", "y", "line_a", "line_b", "method"])
    write_csv(output_dir / "OCR引擎状态.csv", engine_status, ["engine", "success", "items", "error"])
    if difference.get("provided"):
        write_csv(output_dir / "图片差分.csv", difference["components"], ["id", "region_id", "bbox", "area", "centroid"])

    workbook = {"success": False, "error": "disabled"} if args.no_workbook else build_workbook(report_path, output_dir)
    result = {
        "output": str(output_dir),
        "regions": len(cells),
        "uncertain": len(uncertain),
        "ocr_engines": engine_status,
        "coverage": gate["coverage"],
        "lock_permission": gate["permission"],
        "blocking_reasons": gate["blocking_reasons"],
        "workbook": workbook,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if workbook.get("success") or args.no_workbook else 5


if __name__ == "__main__":
    raise SystemExit(main())
