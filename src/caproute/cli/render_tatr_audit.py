from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from caproute.evaluation.grits import grits_loc
from caproute.evaluation.structure_shape import ground_truth_cells, structure_files_for_page


def draw(axis, cells, title):
    for cell in cells:
        x0, y0, x1, y1 = cell["bbox"]
        axis.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="black", linewidth=0.8))
    axis.set(xlim=(0, 1), ylim=(1, 0), aspect="equal", title=title)
    axis.axis("off")


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--predictions", default="outputs/tatr_structure_preflight/predictions.jsonl")
    cli.add_argument("--detection-root", default="data/raw/pubtables/PubTables-1M-Image_Page_Detection_PASCAL_VOC/val")
    cli.add_argument("--structure-root", default="data/raw/pubtables/PubTables-1M-Structure/val")
    cli.add_argument("--output", default="docs/figures/tatr_span_loc_audit.png")
    args = cli.parse_args()
    candidates = []
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        paths = structure_files_for_page(args.detection_root, args.structure_root, row["document_id"], int(row["page_index"]))
        truths = [ground_truth_cells(path) for path in paths if path.exists()]
        for index in range(min(len(truths), len(row["predicted_cells"]))):
            prediction = row["predicted_cells"][index]
            score = float(grits_loc(truths[index], prediction)[0])
            candidates.append((score, row["document_id"], row["page_index"], index, truths[index], prediction))
    candidates.sort(key=lambda item: item[0])
    selected = [("worst", candidates[0]), ("median", candidates[len(candidates) // 2]), ("best", candidates[-1])]
    figure, axes = plt.subplots(3, 2, figsize=(8, 10))
    for row_index, (label, item) in enumerate(selected):
        score, document_id, page_index, table_index, truth, prediction = item
        suffix = f"{document_id} p{page_index} t{table_index} · Loc {score:.3f}"
        draw(axes[row_index, 0], truth, f"{label} / ground truth\n{suffix}")
        draw(axes[row_index, 1], prediction, f"{label} / TATR span-aware\n{suffix}")
    figure.tight_layout()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    print(output.resolve())


if __name__ == "__main__": main()
