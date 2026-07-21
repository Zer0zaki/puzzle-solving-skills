#!/usr/bin/env python3
"""Apply a reviewed inventory to an existing visual transcription report.

The original run remains immutable. Reviewed outputs are written to a new directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from transcribe_visual_puzzle import (
    annotate,
    apply_review_manifest,
    build_gate,
    build_workbook,
    load_review_manifest,
    read_image,
    write_csv,
    write_image,
    write_json,
)


CELL_HEADERS = [
    "region_id", "row", "col", "bbox", "crop", "transcription_status",
    "auto_transcription_status", "text", "reviewed_text", "effective_text",
    "ocr_status", "ocr_confidence", "ocr_candidates", "dominant_color",
    "color_clusters", "line_ids", "arrow_ids", "intersection_ids", "confidence",
    "review_note", "user_confirmed",
]


def copy_evidence(source_dir: Path, output_dir: Path, cells: list[dict[str, Any]]) -> None:
    for name in [
        "original.png", "normalized.png", "geometry_edges.png", "after_aligned.png",
        "diff_mask.png", "diff_overlay.png",
    ]:
        source = source_dir / name
        if source.exists():
            shutil.copy2(source, output_dir / name)
    source_cells = source_dir / "cells"
    target_cells = output_dir / "cells"
    if source_cells.exists():
        shutil.copytree(source_cells, target_cells, dirs_exist_ok=True)
        for cell in cells:
            crop_name = Path(str(cell.get("crop", ""))).name
            if crop_name:
                cell["crop"] = str(target_cells / crop_name)


def export_tables(report: dict[str, Any], output_dir: Path) -> None:
    write_csv(output_dir / "逐格转录.csv", report["cells"], CELL_HEADERS)
    write_csv(
        output_dir / "不确定字符.csv",
        report.get("uncertain", []),
        ["region_id", "bbox", "best_reading", "candidates", "reason", "crop", "user_resolution"],
    )
    write_csv(output_dir / "颜色聚类.csv", report.get("colors", []), ["region_id", "rank", "rgb", "hex", "proportion"])
    geometry_rows: list[dict[str, Any]] = []
    for kind in ("lines", "arrows", "intersections"):
        for record in report.get("geometry", {}).get(kind, []):
            geometry_rows.append({"kind": kind[:-1], **record})
    write_csv(
        output_dir / "几何元素.csv",
        geometry_rows,
        ["kind", "id", "region_id", "points", "angle", "length", "line_id", "start", "end", "head_center", "direction_degrees", "x", "y", "line_a", "line_b", "method"],
    )
    write_csv(output_dir / "OCR引擎状态.csv", report.get("engines", []), ["engine", "success", "items", "error"])
    if report.get("difference", {}).get("provided"):
        write_csv(output_dir / "图片差分.csv", report["difference"].get("components", []), ["id", "region_id", "bbox", "area", "centroid"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a reviewed inventory and recalculate the visual lock gate.")
    parser.add_argument("report", type=Path, help="report.json from the automatic transcription run")
    parser.add_argument("review_manifest", type=Path, help="completed inventory_review_template.json")
    parser.add_argument("--output", type=Path, required=True, help="new directory for reviewed outputs")
    args = parser.parse_args()

    report_path = args.report.resolve()
    source_dir = report_path.parent
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image_sha256 = str(report.get("input", {}).get("image_sha256", ""))
    if not image_sha256:
        raise SystemExit("source report does not contain input.image_sha256")

    manifest, errors = load_review_manifest(args.review_manifest.resolve(), image_sha256)
    apply_review_manifest(report["cells"], report.get("uncertain", []), manifest, errors)
    report["gate"] = build_gate(
        report["cells"],
        report["grid"],
        report.get("engines", []),
        float(report.get("gate", {}).get("coverage_threshold", 0.95)),
        manifest,
        errors,
    )
    report["review"] = {"manifest": str(args.review_manifest.resolve()), "errors": errors, "applied_to": str(report_path)}
    copy_evidence(source_dir, output_dir, report["cells"])
    normalized_path = output_dir / "normalized.png"
    if normalized_path.exists():
        annotated = annotate(read_image(normalized_path), report["cells"], report.get("geometry", {}))
        write_image(output_dir / "annotated_regions.png", annotated)
    write_json(output_dir / "inventory_review_applied.json", manifest or {})
    write_json(output_dir / "report.json", report)
    export_tables(report, output_dir)
    workbook = build_workbook(output_dir / "report.json", output_dir)
    result = {
        "output": str(output_dir),
        "coverage": report["gate"]["coverage"],
        "lock_permission": report["gate"]["permission"],
        "blocking_reasons": report["gate"]["blocking_reasons"],
        "workbook": workbook,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if workbook.get("success") else 5


if __name__ == "__main__":
    raise SystemExit(main())
