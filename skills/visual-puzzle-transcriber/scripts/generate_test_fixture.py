#!/usr/bin/env python3
"""Generate deterministic visual-puzzle fixtures for the skill self-test."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def write_image(path: Path, image: np.ndarray) -> None:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"cannot encode {path}")
    encoded.tofile(str(path))


def create_flat(after: bool = False) -> np.ndarray:
    size = 900
    margin = 45
    inner = size - margin * 2
    cell = inner // 3
    canvas = np.full((size, size, 3), 248, dtype=np.uint8)
    fills = [
        (225, 238, 250), (232, 246, 226), (247, 229, 229),
        (239, 231, 250), (229, 244, 244), (240, 240, 224),
        (231, 238, 249), (244, 232, 219), (228, 242, 235),
    ]
    labels = ["A", "B", "C", "1", "2", "3", "N", "GO", "END"]
    for row in range(3):
        for col in range(3):
            index = row * 3 + col
            x1, y1 = margin + col * cell, margin + row * cell
            x2, y2 = margin + (col + 1) * cell, margin + (row + 1) * cell
            cv2.rectangle(canvas, (x1, y1), (x2, y2), fills[index], -1)
            label = labels[index]
            scale = 3.0 if len(label) == 1 else 1.8
            thickness = 6
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.putText(canvas, label, (center_x - text_width // 2, center_y + text_height // 2), cv2.FONT_HERSHEY_SIMPLEX, scale, (28, 35, 40), thickness, cv2.LINE_AA)
    for index in range(4):
        position = margin + index * cell
        cv2.line(canvas, (margin, position), (margin + inner, position), (25, 32, 35), 6)
        cv2.line(canvas, (position, margin), (position, margin + inner), (25, 32, 35), 6)
    cv2.arrowedLine(canvas, (margin + cell + 45, margin + 2 * cell + cell // 2), (margin + 2 * cell - 45, margin + 2 * cell + cell // 2), (20, 55, 170), 12, tipLength=0.2)
    cv2.circle(canvas, (margin + cell // 2, margin + cell // 2), 30, (20, 180, 230), -1)
    if after:
        center = (margin + 2 * cell + cell // 2, margin + cell + cell // 2)
        cv2.circle(canvas, center, 66, (25, 25, 220), 15)
        cv2.line(canvas, (center[0] - 42, center[1] - 42), (center[0] + 42, center[1] + 42), (25, 25, 220), 12)
        cv2.line(canvas, (center[0] + 42, center[1] - 42), (center[0] - 42, center[1] + 42), (25, 25, 220), 12)
    return canvas


def warp(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    source = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    target = np.float32([[90, 45], [width + 40, 95], [width - 5, height + 45], [35, height - 20]])
    matrix = cv2.getPerspectiveTransform(source, target)
    return cv2.warpPerspective(image, matrix, (width + 120, height + 100), borderValue=(210, 212, 214))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    before_flat = create_flat(False)
    after_flat = create_flat(True)
    write_image(args.output / "fixture_flat_before.png", before_flat)
    write_image(args.output / "fixture_flat_after.png", after_flat)
    write_image(args.output / "fixture_perspective_before.png", warp(before_flat))
    write_image(args.output / "fixture_perspective_after.png", warp(after_flat))
    print(args.output)


if __name__ == "__main__":
    main()
