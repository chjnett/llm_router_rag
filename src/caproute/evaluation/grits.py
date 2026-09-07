"""GriTS Top/Loc core following Microsoft Table Transformer ``src/grits.py``.

The factored 2D-MSS alignment and relative-span representation follow the
official implementation. Kept dependency-light so cached parser outputs can
be evaluated without loading either parser model.
"""
from __future__ import annotations

import itertools
from collections.abc import Callable

import numpy as np


def _fscore(match: float, true_count: int, pred_count: int) -> tuple[float, float, float]:
    precision = match / pred_count if pred_count else 1.0
    recall = match / true_count if true_count else 1.0
    score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return score, precision, recall


def bbox_iou(left: list[float], right: list[float]) -> float:
    ix0, iy0 = max(left[0], right[0]), max(left[1], right[1])
    ix1, iy1 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def _initialize(length1: int, length2: int) -> tuple[np.ndarray, np.ndarray]:
    scores = np.zeros((length1 + 1, length2 + 1))
    pointers = np.zeros((length1 + 1, length2 + 1))
    pointers[1:, 0] = -1
    pointers[0, 1:] = 1
    return scores, pointers


def _traceback(pointers: np.ndarray) -> tuple[list[int], list[int]]:
    first, second = pointers.shape[0] - 1, pointers.shape[1] - 1
    aligned_first, aligned_second = [], []
    while first or second:
        if pointers[first, second] == -1:
            first -= 1
        elif pointers[first, second] == 1:
            second -= 1
        else:
            first -= 1
            second -= 1
            aligned_first.append(first)
            aligned_second.append(second)
    return aligned_first[::-1], aligned_second[::-1]


def _align_1d(sequence1: list[tuple[int, int]], sequence2: list[tuple[int, int]], rewards: dict) -> float:
    scores, pointers = _initialize(len(sequence1), len(sequence2))
    for first in range(1, len(sequence1) + 1):
        for second in range(1, len(sequence2) + 1):
            diagonal = scores[first - 1, second - 1] + rewards[sequence1[first - 1] + sequence2[second - 1]]
            skip_second = scores[first, second - 1]
            skip_first = scores[first - 1, second]
            best = max(diagonal, skip_first, skip_second)
            scores[first, second] = best
            pointers[first, second] = 0 if diagonal == best else (-1 if skip_first == best else 1)
    return float(scores[-1, -1])


def _align_outer(true_shape: tuple[int, int], pred_shape: tuple[int, int], rewards: dict) -> tuple[list[int], list[int], float]:
    scores, pointers = _initialize(true_shape[0], pred_shape[0])
    for true_row in range(1, true_shape[0] + 1):
        for pred_row in range(1, pred_shape[0] + 1):
            reward = _align_1d(
                [(true_row - 1, column) for column in range(true_shape[1])],
                [(pred_row - 1, column) for column in range(pred_shape[1])],
                rewards,
            )
            diagonal = scores[true_row - 1, pred_row - 1] + reward
            skip_pred = scores[true_row, pred_row - 1]
            skip_true = scores[true_row - 1, pred_row]
            best = max(diagonal, skip_true, skip_pred)
            scores[true_row, pred_row] = best
            pointers[true_row, pred_row] = 0 if diagonal == best else (-1 if skip_true == best else 1)
    true_rows, pred_rows = _traceback(pointers)
    return true_rows, pred_rows, float(scores[-1, -1])


def factored_2dmss(true_grid: np.ndarray, pred_grid: np.ndarray, reward: Callable) -> tuple[float, float, float, float]:
    rewards, transposed = {}, {}
    for tr, tc, pr, pc in itertools.product(
        range(true_grid.shape[0]), range(true_grid.shape[1]),
        range(pred_grid.shape[0]), range(pred_grid.shape[1]),
    ):
        value = reward(true_grid[tr, tc], pred_grid[pr, pc])
        rewards[(tr, tc, pr, pc)] = value
        transposed[(tc, tr, pc, pr)] = value
    true_rows, pred_rows, row_score = _align_outer(true_grid.shape[:2], pred_grid.shape[:2], rewards)
    true_cols, pred_cols, col_score = _align_outer(true_grid.shape[:2][::-1], pred_grid.shape[:2][::-1], transposed)
    upper = _fscore(min(row_score, col_score), true_grid.shape[0] * true_grid.shape[1], pred_grid.shape[0] * pred_grid.shape[1])[0]
    match = sum(rewards[(tr, tc, pr, pc)] for tr, pr in zip(true_rows, pred_rows) for tc, pc in zip(true_cols, pred_cols))
    score, precision, recall = _fscore(match, true_grid.shape[0] * true_grid.shape[1], pred_grid.shape[0] * pred_grid.shape[1])
    return score, precision, recall, upper


def cells_to_grid(cells: list[dict], key: str) -> np.ndarray:
    if not cells:
        return np.empty((0, 0), dtype=object)
    rows = max(max(cell["row_nums"]) for cell in cells) + 1
    columns = max(max(cell["column_nums"]) for cell in cells) + 1
    grid = [[([0.0, 0.0, 0.0, 0.0] if key == "bbox" else [0, 0, 1, 1]) for _ in range(columns)] for _ in range(rows)]
    for cell in cells:
        for row in cell["row_nums"]:
            for column in cell["column_nums"]:
                if key == "bbox":
                    grid[row][column] = cell["bbox"]
                else:
                    grid[row][column] = [
                        min(cell["column_nums"]) - column,
                        min(cell["row_nums"]) - row,
                        max(cell["column_nums"]) + 1 - column,
                        max(cell["row_nums"]) + 1 - row,
                    ]
    return np.asarray(grid, dtype=float)


def grits_top(true_cells: list[dict], pred_cells: list[dict]) -> tuple[float, float, float, float]:
    if not true_cells or not pred_cells:
        return (1.0, 1.0, 1.0, 1.0) if not true_cells and not pred_cells else (0.0, 0.0, 0.0, 0.0)
    return factored_2dmss(cells_to_grid(true_cells, "relspan"), cells_to_grid(pred_cells, "relspan"), bbox_iou)


def grits_loc(true_cells: list[dict], pred_cells: list[dict]) -> tuple[float, float, float, float]:
    if not true_cells or not pred_cells:
        return (1.0, 1.0, 1.0, 1.0) if not true_cells and not pred_cells else (0.0, 0.0, 0.0, 0.0)
    return factored_2dmss(cells_to_grid(true_cells, "bbox"), cells_to_grid(pred_cells, "bbox"), bbox_iou)
