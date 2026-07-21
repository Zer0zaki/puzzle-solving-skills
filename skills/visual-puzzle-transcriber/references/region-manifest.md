# Generic external region manifest

The core pipeline must not contain puzzle-specific segmentation rules. Any specialized detector runs outside the skill and may only provide geometry through `--regions-manifest`.

## Required structure

```json
{
  "schema_version": "1.0",
  "image_sha256": "hex digest of the original input image",
  "coordinate_space": "input",
  "detector": {
    "name": "external detector name",
    "version": "detector version or code hash",
    "confidence": 0.8,
    "parameters": {}
  },
  "regions": [
    {
      "region_id": "P01-R001",
      "row": 1,
      "col": 1,
      "kind": "region",
      "bbox": [100, 80, 60, 40],
      "metadata": {}
    }
  ]
}
```

Each region requires a unique `region_id` and either `bbox: [x, y, width, height]` or `polygon: [[x, y], ...]`. `coordinate_space` is `input` or `normalized`. Input-space points are transformed with the recorded perspective matrix when correction was applied.

## Boundary rules

- The core validates the image SHA-256, IDs, coordinate space, geometry, and image bounds.
- Detector parameters and code identity remain in `detector`; do not hide them in prose.
- Detector-specific semantic classes belong in `metadata`. The core preserves but never interprets them.
- A region manifest is detector evidence, not human inventory confirmation. Reviewed coverage remains zero until the separate review manifest is imported.
- No external adapter is auto-discovered or auto-run. The operator must invoke it explicitly and pass its output path.

## Anti-contamination rule

If a rule mentions a particular puzzle title, answer, color value, named visual object, row count, feeder, or extraction convention, it belongs with that puzzle or adapter—not in the core skill.
