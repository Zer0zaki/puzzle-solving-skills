#!/usr/bin/env python3
"""End-to-end smoke test for the visual transcription pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    args = parser.parse_args()
    fixture_dir = args.workdir / "fixtures"
    draft_dir = args.workdir / "draft"
    result_dir = args.workdir / "result"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "generate_test_fixture.py"), str(fixture_dir)], check=True)
    command = [
        sys.executable,
        str(SCRIPT_DIR / "transcribe_visual_puzzle.py"),
        str(fixture_dir / "fixture_perspective_before.png"),
        "--after", str(fixture_dir / "fixture_perspective_after.png"),
        "--output", str(draft_dir),
        "--rows", "3",
        "--cols", "3",
    ]
    process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=360)
    print(process.stdout)
    if process.stderr:
        print(process.stderr, file=sys.stderr)
    require(process.returncode == 0, f"pipeline returned {process.returncode}")
    draft_report = json.loads((draft_dir / "report.json").read_text(encoding="utf-8"))
    require(draft_report["gate"]["coverage"] == 0, "unreviewed draft must not claim coverage")
    require(draft_report["gate"]["permission"] == "禁止", "unreviewed draft must remain blocked")
    review_path = draft_dir / "inventory_review_template.json"
    require(review_path.exists(), "review template missing")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["inventory_verified"] = True
    review["reviewed_by"] = "self-test"
    review["reviewed_at"] = "2026-07-21T00:00:00+08:00"
    review["grid_review"]["accepted"] = True
    for item in review["expected_regions"]:
        item["review_status"] = "不确定"
    approved_review_path = args.workdir / "approved_review.json"
    approved_review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("vpt", SCRIPT_DIR / "transcribe_visual_puzzle.py")
    require(spec is not None and spec.loader is not None, "cannot import transcriber for gate test")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing_review = json.loads(json.dumps(review, ensure_ascii=False))
    missing_review["expected_regions"].append({"region_id": "PANEL-MISSING", "review_status": "不确定"})
    missing_gate = module.build_gate(draft_report["cells"], draft_report["grid"], draft_report["engines"], 0.95, missing_review, [])
    require(missing_gate["permission"] == "禁止", "missing panel must block locking")
    require(missing_gate["coverage"] < 1, "missing panel must lower coverage")
    require("PANEL-MISSING" in missing_gate["missing_region_ids"], "missing panel ID not reported")

    regions_manifest = {
        "schema_version": "1.0",
        "image_sha256": draft_report["input"]["image_sha256"],
        "coordinate_space": "input",
        "detector": {"name": "synthetic-test-detector", "version": "1", "confidence": 0.8, "parameters": {"fixture": True}},
        "regions": [
            {"region_id": "EXT-001", "row": 1, "col": 1, "bbox": [160, 140, 120, 90], "kind": "test-region"},
            {"region_id": "EXT-002", "row": 1, "col": 2, "polygon": [[300, 140], [420, 140], [420, 230], [300, 230]], "kind": "test-region"},
            {"region_id": "EXT-003", "row": 2, "col": 1, "bbox": [160, 250, 120, 90], "kind": "test-region"},
        ],
    }
    regions_manifest_path = args.workdir / "external_regions.json"
    regions_manifest_path.write_text(json.dumps(regions_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    external_dir = args.workdir / "external-regions"
    external_command = [
        sys.executable,
        str(SCRIPT_DIR / "transcribe_visual_puzzle.py"),
        str(fixture_dir / "fixture_perspective_before.png"),
        "--output", str(external_dir),
        "--regions-manifest", str(regions_manifest_path),
        "--ocr-engines", "rapidocr",
        "--no-workbook",
    ]
    external_process = subprocess.run(external_command, capture_output=True, text=True, check=False, timeout=360)
    require(external_process.returncode == 0, f"external region pipeline returned {external_process.returncode}")
    external_report = json.loads((external_dir / "report.json").read_text(encoding="utf-8"))
    require(external_report["grid"]["mode"] == "external_region_manifest", "generic region manifest mode not used")
    require(len(external_report["cells"]) == 3, "external region count mismatch")
    require(external_report["grid"]["detector"]["name"] == "synthetic-test-detector", "detector provenance not preserved")
    require(external_report["gate"]["coverage"] == 0, "external detector must not self-confirm reviewed coverage")

    approved_command = [
        sys.executable,
        str(SCRIPT_DIR / "apply_transcription_review.py"),
        str(draft_dir / "report.json"),
        str(approved_review_path),
        "--output",
        str(result_dir),
    ]
    approved_process = subprocess.run(approved_command, capture_output=True, text=True, check=False, timeout=360)
    print(approved_process.stdout)
    if approved_process.stderr:
        print(approved_process.stderr, file=sys.stderr)
    require(approved_process.returncode == 0, f"approved pipeline returned {approved_process.returncode}")
    report = json.loads((result_dir / "report.json").read_text(encoding="utf-8"))
    require(len(report["cells"]) == 9, "expected 9 grid cells")
    require(report["grid"]["mode"] == "explicit", "explicit 3x3 grid not used")
    require(len(report["colors"]) >= 9, "color clustering missing")
    require(len(report["geometry"]["lines"]) > 0, "line detection missing")
    require(len(report["geometry"]["arrows"]) > 0, "arrow detection missing")
    arrow_angle = float(report["geometry"]["arrows"][0]["direction_degrees"])
    require(arrow_angle <= 25 or arrow_angle >= 335, f"arrow direction should be rightward, got {arrow_angle}")
    require(report["difference"]["provided"], "difference branch not executed")
    require(len(report["difference"]["components"]) > 0, "no changed component found")
    require(len(report["engines"]) >= 2, "multi-engine OCR was not attempted")
    require(sum(bool(item.get("success")) for item in report["engines"]) >= 2, "fewer than two OCR engines succeeded")
    for required in [
        "annotated_regions.png",
        "逐格转录.csv",
        "不确定字符.csv",
        "颜色聚类.csv",
        "几何元素.csv",
        "图片差分.csv",
        "visual_transcription.xlsx",
        "workbook_formula_errors.ndjson",
        "inventory_review_applied.json",
    ]:
        require((result_dir / required).exists(), f"missing {required}")
    formula_scan = (result_dir / "workbook_formula_errors.ndjson").read_text(encoding="utf-8")
    require("matched 0 entries" in formula_scan, "workbook formula error scan did not pass")
    summary = {
        "passed": True,
        "cells": len(report["cells"]),
        "uncertain": len(report["uncertain"]),
        "successful_engines": [item["engine"] for item in report["engines"] if item.get("success")],
        "lines": len(report["geometry"]["lines"]),
        "arrows": len(report["geometry"]["arrows"]),
        "intersections": len(report["geometry"]["intersections"]),
        "diff_components": len(report["difference"]["components"]),
        "coverage": report["gate"]["coverage"],
        "lock_permission": report["gate"]["permission"],
        "draft_coverage": draft_report["gate"]["coverage"],
        "missing_panel_coverage": missing_gate["coverage"],
        "external_region_count": len(external_report["cells"]),
        "result_dir": str(result_dir),
    }
    (args.workdir / "self_test_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
