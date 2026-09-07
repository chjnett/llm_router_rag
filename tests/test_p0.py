from __future__ import annotations

from pathlib import Path

from caproute.benchmark.harness import percentile, run_parser
from caproute.cache import PredictionCache
from caproute.core.config import config_hash
from caproute.datasets.pubtables import PubTablesSample, load_pubtables_subset
from caproute.datasets.pubtables import _document_id
from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser
from caproute.evaluation.structure_shape import _docling_region_cells, shape_similarity
from caproute.evaluation.grits import grits_loc, grits_top
from caproute.cli.p1_oracle import is_sufficient


class FakeParser(DocumentParser):
    name, role, version = "fake", "cheap", "1"

    def parse(self, item):
        return CanonicalDocument(
            item.document_id, str(item.source_path), self.name, self.version, self.role,
            [CanonicalPage(0, 100, 100, [Block("b1", "text", [0, 0, 1, 1], "hello")])],
        )


def test_config_hash_is_order_independent():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})


def test_canonical_ir_round_trip():
    original = FakeParser().parse(DocumentInput("d", Path("x.pdf")))
    assert CanonicalDocument.from_dict(original.to_dict()).to_dict() == original.to_dict()


def test_pubtables_loader_is_document_disjoint(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    names = ("PMC1_page_0.png", "PMC1_page_1.png", "PMC2_page_0.png")
    for name in names:
        (images / name).write_bytes(b"x")
        (annotations / f"{Path(name).stem}.xml").write_text(
            f"<annotation><filename>{name}</filename><object><name>table</name>"
            "<bndbox><xmin>0</xmin><ymin>0</ymin><xmax>10</xmax><ymax>10</ymax></bndbox>"
            "</object></annotation>",
            encoding="utf-8",
        )
    split = tmp_path / "val_filelist.txt"
    split.write_text(
        "\n".join(f"annotations/{Path(name).stem}.xml" for name in names),
        encoding="utf-8",
    )
    rows = load_pubtables_subset(tmp_path, split, images, None, 3, 42, True)
    assert len(rows) == 2
    assert len({row.item.document_id for row in rows}) == 2


def test_cache_and_harness_reuse_raw_prediction(tmp_path):
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"fixture")
    sample = PubTablesSample(DocumentInput("d", source), source, {"table_boxes_xywh": []})
    cache = PredictionCache(tmp_path / "cache")
    first, failures, metrics = run_parser(FakeParser(), [sample], cache, power_interval_seconds=0.01)
    second, _, second_metrics = run_parser(FakeParser(), [sample], cache, power_interval_seconds=0.01)
    assert not failures and not first[0]["cache_hit"]
    assert second[0]["cache_hit"]
    assert metrics["measured_uncached_items"] == 1
    assert metrics["gpu_seconds_per_page"] is None
    assert metrics["wall_seconds_per_page"] is not None
    assert metrics["warmup_completed"] == 0
    assert second_metrics["measured_uncached_items"] == 0


def test_percentile_contract():
    assert percentile([1, 2, 3], 0.5) == 2
    assert percentile([], 0.5) is None


def test_structure_shape_similarity_penalizes_missing_and_wrong_shape():
    truth = [{"row_count": 4, "column_count": 2}]
    assert shape_similarity(truth, truth) == 1.0
    assert shape_similarity(truth, []) == 0.0
    assert shape_similarity(truth, [{"row_count": 2, "column_count": 2}]) == 0.75


def test_docling_tight_boxes_expand_to_cell_regions():
    table = {
        "prov": [{"page_no": 1, "bbox": {"l": 0, "t": 100, "r": 100, "b": 0, "coord_origin": "BOTTOMLEFT"}}],
        "data": {"table_cells": [
            {"start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 0, "end_col_offset_idx": 1,
             "bbox": {"l": 10, "t": 10, "r": 20, "b": 20}},
            {"start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 1, "end_col_offset_idx": 2,
             "bbox": {"l": 60, "t": 10, "r": 70, "b": 20}},
            {"start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 0, "end_col_offset_idx": 1,
             "bbox": {"l": 10, "t": 60, "r": 20, "b": 70}},
            {"start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 1, "end_col_offset_idx": 2,
             "bbox": {"l": 60, "t": 60, "r": 70, "b": 70}},
        ]},
    }
    cells = _docling_region_cells(table, {"1": {"size": {"height": 100}}})
    assert cells[0]["bbox"] == [0.0, 0.0, 0.4, 0.4]
    assert cells[-1]["bbox"] == [0.4, 0.4, 1.0, 1.0]


def test_p1_sufficiency_requires_all_frozen_conditions():
    rule = {"require_exact_table_count": True, "min_grits_top": 0.8, "min_grits_loc": 0.5}
    metrics = {"exact_table_count": True, "grits_top_mean": 0.8, "grits_loc_mean": 0.5}
    assert is_sufficient(metrics, rule)
    assert not is_sufficient({**metrics, "exact_table_count": False}, rule)
    assert not is_sufficient({**metrics, "grits_top_mean": 0.799}, rule)


def test_grits_identity_and_missing_table_contract():
    cells = [
        {"row_nums": [0], "column_nums": [0], "bbox": [0.0, 0.0, 0.5, 1.0]},
        {"row_nums": [0], "column_nums": [1], "bbox": [0.5, 0.0, 1.0, 1.0]},
    ]
    assert grits_top(cells, cells)[0] == 1.0
    assert grits_loc(cells, cells)[0] == 1.0
    assert grits_top(cells, [])[0] == 0.0


def test_official_pubtables_filename_identity():
    assert _document_id("PMC4504083_6.jpg") == "PMC4504083"


def test_pubtables_loader_supports_recorded_exclusions(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    annotations = tmp_path / "val"
    annotations.mkdir()
    split = tmp_path / "val_filelist.txt"
    rows = []
    for document_id in ("PMC1", "PMC2"):
        name = f"{document_id}_0.jpg"
        (images / name).write_bytes(b"x")
        xml = annotations / f"{document_id}_0.xml"
        xml.write_text(f"<annotation><filename>{name}</filename></annotation>", encoding="utf-8")
        rows.append(f"val/{document_id}_0.xml")
    split.write_text("\n".join(rows), encoding="utf-8")
    result = load_pubtables_subset(
        tmp_path, split, images, None, 2, 42, True, {"PMC1"}
    )
    assert [row.item.document_id for row in result] == ["PMC2"]
