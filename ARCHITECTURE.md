# Architecture

## Original Ingestion Architecture (P1 Oracle FAIL)

```text
Scientific PDF
      │
      ▼
Cheap Native Scan
(PyMuPDF / GROBID)
      │
      ▼
Feasibility Guard
      │
      ▼
Capability Pre-Router
   /              \
Cheap 가능       Strong 필요
   │                │
   ▼                │
Cheap Parser        │
   │                │
   ▼                │
Output Verifier     │
  /        \        │
Pass       Fail─────┘
 │                  │
 │                  ▼
 │             Strong Parser/VLM
 │                  │
 └──────────┬───────┘
            ▼
       Canonical IR
            │
            ▼
         Chunking
            │
            ▼
        Embedding
            │
            ▼
        Vector DB
            │
            ▼
         Retriever
            │
            ▼
          Answer
```

---

## 1. Cheap Native Scan

목적:

Strong model을 실행하기 전에 가능한 cheap feature를 뽑는다.

후보:

- PyMuPDF
- GROBID
- PDF metadata
- native text layer

추출 feature 예:

- text length
- text density
- column count
- bbox density
- table count
- figure count
- image ratio
- native text coverage
- font diversity
- reading-order complexity
- equation hints
- table geometry

---

## 2. Feasibility Guard

문서군 / batch에서 cascade 경제성이 없는 경우 bypass한다.

기본 아이디어:

```text
observed_saving
=
cheap_acceptance_rate
-
cheap_call_rate * (C_cheap / C_strong)
```

보수적 lower bound가 0 이하이면 Always Strong.

---

## 3. Capability Pre-Router

예측 대상:

> Strong processing이 실제로 필요한가?

단순 `table vs text` 분류가 아니다.

---

## 4. Cheap Parser

후보:

- PyMuPDF native text
- GROBID
- lightweight table parser
- deterministic structure parser

---

## 5. Output Verifier

Cheap output의 구조적 신뢰성을 검사한다.

feature 예:

- schema validity
- text coverage
- row consistency
- column consistency
- header consistency
- empty cell ratio
- numeric consistency
- source/output coverage
- parse warnings

---

## 6. Strong Parser / VLM

후보는 P0에서 실제 성능/속도를 측정해 고른다.

예:

- Docling
- Nougat
- TableFormer 계열
- quantized VLM

모델 크기보다 실제 RTX 3090 latency를 우선한다.

---

## 7. Canonical IR

모든 parser output은 동일 schema로 변환한다.

```json
{
  "document_id": "paper_001",
  "page_id": 12,
  "source_parser": "cheap",
  "route": "cheap_accept",
  "blocks": [
    {
      "block_id": "b1",
      "type": "text",
      "bbox": [0, 0, 100, 100],
      "text": "...",
      "confidence": 0.94
    }
  ],
  "tables": [],
  "figures": [],
  "metadata": {}
}
```

반드시 provenance를 남긴다.

---

## 8. Current Candidate: Query-Time Selective Rescue

SciVQA validation에서 Caption/ColSmol 결과의 보완성과 frozen selector의 품질 일반화는 확인했다. 그러나 구현된 13-feature selector는 Strong score·margin·entropy를 요구하므로 post-retrieval fuser이며 Strong 실행을 건너뛰지 못한다.

```text
Question
   ↓
Cheap caption retrieve
   ↓
Early confidence / Query Type
   ├─ sufficient → Answer
   └─ uncertain / visual-heavy
          ↓
      Top-K pages
          ↓
      Strong/VLM rescue
          ↓
        Answer
```

## 9. Candidate Visual Retrieval Branch

ColPali는 parser가 아니라 visual retriever로 취급한다. 작은 multimodal preflight에서 Always Text, Always ColPali, Rule Selective, Oracle Selective의 retrieval 품질·GPU 시간·index bytes를 비교한 뒤에만 routing 경로로 승격한다.

## 10. Required Two-Stage Router

```text
Question + Cheap caption scores
              │
              ▼
    Early Router (Cheap-only)
        /                 \
skip Strong            run Strong
    │                       │
Caption rank        ColSmol query + MaxSim
    │                       │
    │              Optional Late Fuser
    └───────────────┬───────┘
                    ▼
               Final evidence
```

Early Router 입력은 Strong 실행 전에 얻을 수 있는 특징으로 제한한다.

- candidate count
- question length
- table/figure/graph/chart keyword
- Caption BGE top score, margin, normalized entropy

현재 13-feature 모델의 Strong score·margin·entropy와 두 경로 difference 특징은 Late Fuser에서만 사용할 수 있다. Late Fuser의 선택률은 비용 절감률로 보고하지 않는다.

다음 one-shot Gate는 미개봉 SciVQA test에서 측정한다.

- Always Strong 대비 R@1 및 MRR retention ≥ 95%
- 실제로 생략한 ColSmol query encoding + MaxSim ≥ 15%
- peak allocated VRAM ≤ 22GB
- policy와 threshold는 test manifest 생성 전에 lock
