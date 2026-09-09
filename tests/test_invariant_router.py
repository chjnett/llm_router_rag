from caproute.cli.screen_scivqa_invariant_router import invariant_features, paper_split


def test_invariant_features_do_not_depend_on_candidate_count():
    row = {
        "question": "Which value appears in the table?",
        "candidate_images": 12,
        "caption_signal": {"top_score": 0.8, "top_margin": 0.2, "normalized_entropy": 0.6},
    }
    changed = {**row, "candidate_images": 10000}
    assert invariant_features(row) == invariant_features(changed)


def test_paper_split_is_disjoint_and_deterministic():
    rows = [
        {"paper_id": paper, "question": f"q-{paper}-{index}"}
        for paper in ("a", "b", "c", "d")
        for index in range(2)
    ]
    first = paper_split(rows, seed=42, train_fraction=0.5)
    second = paper_split(rows, seed=42, train_fraction=0.5)
    assert first == second
    train_papers = {row["paper_id"] for row in first[0]}
    calibration_papers = {row["paper_id"] for row in first[1]}
    assert train_papers.isdisjoint(calibration_papers)
