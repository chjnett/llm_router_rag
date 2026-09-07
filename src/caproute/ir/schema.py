from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BlockType = Literal["text", "title", "table", "figure", "equation", "caption", "unknown"]


@dataclass
class Block:
    block_id: str
    type: BlockType
    bbox: list[float]
    text: str = ""
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalPage:
    page_id: int
    width: float
    height: float
    blocks: list[Block] = field(default_factory=list)


@dataclass
class CanonicalDocument:
    document_id: str
    source_path: str
    source_parser: str
    parser_version: str
    route: str
    pages: list[CanonicalPage]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CanonicalDocument":
        pages = [
            CanonicalPage(
                page_id=page["page_id"], width=page["width"], height=page["height"],
                blocks=[Block(**block) for block in page.get("blocks", [])],
            )
            for page in value.get("pages", [])
        ]
        return cls(**{**value, "pages": pages})

