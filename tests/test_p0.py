from __future__ import annotations

from pathlib import Path

from caproute.benchmark.harness import percentile, run_parser
from caproute.cache import PredictionCache
from caproute.core.config import config_hash
from caproute.datasets.pubtables import PubTablesSample, load_pubtables_subset
from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser


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
    assert second_metrics["measured_uncached_items"] == 0


def test_percentile_contract():
    assert percentile([1, 2, 3], 0.5) == 2
    assert percentile([], 0.5) is None
