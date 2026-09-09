from caproute.cli.freeze_scivqa_external_manifest import build_manifest, normalize_paper_id


def test_normalize_paper_id_removes_version_and_pdf() -> None:
    assert normalize_paper_id("2001.12345v3") == "2001.12345"
    assert normalize_paper_id("Y11-1002.pdf") == "Y11-1002"


def test_build_manifest_excludes_overlap_and_unanswerable() -> None:
    rows = [
        {"paper_id": "aV1", "image_file": "a.png", "caption": "A", "figure_id": "fa",
         "instance_id": "1", "question": "q1", "qa_pair_type": "unanswerable"},
        {"paper_id": "b", "image_file": "b.png", "caption": "B", "figure_id": "fb",
         "instance_id": "2", "question": "q2", "qa_pair_type": "closed visual"},
        {"paper_id": "c", "image_file": "c.png", "caption": "C", "figure_id": "fc",
         "instance_id": "3", "question": "q3", "qa_pair_type": "closed visual"},
    ]
    corpus, queries = build_manifest(
        rows,
        {"images/b.png", "images/c.png"},
        "images",
        {"b"},
        {"unanswerable"},
    )
    assert [row["image_file"] for row in corpus] == ["c.png"]
    assert [row["query_id"] for row in queries] == ["3"]
    assert queries[0]["relevant_index"] == 0
