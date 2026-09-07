from __future__ import annotations

import argparse
from pathlib import Path

from caproute.cli.compare_p0 import _latest_prediction_windows, _load_predictions
from caproute.evaluation.grits import grits_loc
from caproute.evaluation.structure_shape import ground_truth_cells, prediction_table_cells, structure_files_for_page


def _draw(ax, cells: list[dict], title: str) -> None:
    from matplotlib.patches import Rectangle

    ax.set_title(title, loc="left", fontsize=9, fontweight="bold", color="#111111")
    for cell in cells:
        left, top, right, bottom = cell["bbox"]
        ax.add_patch(Rectangle((left, top), right - left, bottom - top,
                               fill=False, edgecolor="#111111", linewidth=0.8))
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(1.02, -0.02)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d0d0cc")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="outputs/p0")
    parser.add_argument("--detection-root", required=True)
    parser.add_argument("--structure-root", required=True)
    parser.add_argument("--output", default="outputs/p0/grits_loc_visual_audit.png")
    args = parser.parse_args()

    strong = _load_predictions(_latest_prediction_windows(Path(args.output_root), "docling"))
    candidates = []
    for (document_id, page_index), row in strong.items():
        paths = structure_files_for_page(args.detection_root, args.structure_root, document_id, int(page_index))
        if not paths or any(not path.exists() for path in paths):
            continue
        truth_tables = [ground_truth_cells(path) for path in paths]
        predicted_tables = prediction_table_cells(row)
        for table_index in range(min(len(truth_tables), len(predicted_tables))):
            truth, prediction = truth_tables[table_index], predicted_tables[table_index]
            if truth and prediction:
                score = float(grits_loc(truth, prediction)[0])
                candidates.append((score, document_id, page_index, table_index, truth, prediction))
    candidates.sort(key=lambda row: row[0])
    selected = [candidates[0], candidates[len(candidates) // 2], candidates[-1]]

    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": "#111111"})
    figure, axes = plt.subplots(3, 2, figsize=(7.2, 9.2), facecolor="white")
    labels = ("Worst", "Median", "Best")
    for row_index, (label, item) in enumerate(zip(labels, selected)):
        score, document_id, page_index, table_index, truth, prediction = item
        suffix = f"{document_id} p{page_index} t{table_index} · Loc {score:.3f}"
        _draw(axes[row_index, 0], truth, f"{label} / Ground truth\n{suffix}")
        _draw(axes[row_index, 1], prediction, f"{label} / Docling reconstructed\n{suffix}")
    figure.suptitle("GriTS-Loc cell-region visual audit", x=0.06, ha="left", fontsize=15, fontweight="bold")
    figure.text(0.06, 0.955, "Normalized cell regions · black outlines only", fontsize=9, color="#666666")
    figure.tight_layout(rect=(0.04, 0.02, 0.98, 0.93), h_pad=2.0)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    print(output)
    for label, item in zip(labels, selected):
        print(label, item[1], item[2], item[3], f"loc={item[0]:.6f}")


if __name__ == "__main__":
    main()
