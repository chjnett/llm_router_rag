from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import pymupdf

from caproute.core.config import load_config
from caproute.datasets.qasper import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and verify the frozen R1-P arXiv PDFs")
    parser.add_argument("--config", default="configs/r1_page_mapping.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    output_root = Path(config["outputs"]["root"])
    manifest = json.loads((output_root / "sample_manifest.json").read_text(encoding="utf-8"))
    pdf_root = Path(config["outputs"]["pdf_root"])
    pdf_root.mkdir(parents=True, exist_ok=True)
    results = []
    for paper in manifest["papers"]:
        target = pdf_root / f"{paper['paper_id']}.pdf"
        row = {"paper_id": paper["paper_id"], "url": paper["pdf_url"], "path": str(target), "success": False}
        try:
            if not target.exists():
                request = urllib.request.Request(paper["pdf_url"], headers={"User-Agent": "CapRoute-RAG research/0.1"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    target.write_bytes(response.read())
            with pymupdf.open(target) as document:
                row.update({
                    "success": True, "sha256": sha256_file(target), "bytes": target.stat().st_size,
                    "pages": document.page_count,
                    "native_text_characters": sum(len(page.get_text("text")) for page in document),
                })
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        results.append(row)
        print(json.dumps(row, ensure_ascii=False))
    summary = {"attempted": len(results), "successful": sum(row["success"] for row in results), "papers": results}
    (output_root / "download_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "papers"}, indent=2))
    raise SystemExit(0 if summary["successful"] >= int(config["gate"]["min_pdf_parse_success"]) else 2)


if __name__ == "__main__":
    main()
