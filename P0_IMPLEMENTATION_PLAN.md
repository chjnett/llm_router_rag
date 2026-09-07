# P0 Implementation Plan

## 현재 상태

- 신규 저장소: `C:\llm_models\caproute-rag`
- reference-only 저장소: `C:\llm_models\llm_router`
- 아직 PubTables-1M subset과 Docling model artifact는 준비되지 않았다.
- P0는 다운로드 없이 synthetic fixture로 검증 가능하고, 실제 데이터 경로가 주어지면 300~500 sample screening을 실행할 수 있게 만든다.

## 생성/변경 파일

| 경로 | 책임 |
|---|---|
| `pyproject.toml` | 패키지, core/strong/dev dependency 정의 |
| `configs/p0_screening.yaml` | seed, parser, cache, benchmark, dataset 설정 |
| `src/caproute/core/*` | config hash, atomic serialization, seed, environment metadata |
| `src/caproute/ir/schema.py` | parser-independent Canonical IR와 provenance |
| `src/caproute/datasets/pubtables.py` | 공식 PASCAL VOC + split file 기반 PubTables subset loader |
| `src/caproute/parsers/*` | Cheap/Strong interface, PyMuPDF cheap, optional Docling strong |
| `src/caproute/evaluation/parsing.py` | text coverage와 table detection/structure proxy 평가 |
| `src/caproute/benchmark/*` | latency, p50/p95, peak VRAM, power, failure 기록 |
| `src/caproute/cache.py` | input/config/parser fingerprint 기반 raw prediction cache |
| `src/caproute/cli/screen.py` | 300~500 sample screening entry point |
| `tests/*` | offline unit/integration tests |

## 실행 명령

```powershell
cd C:\llm_models\caproute-rag
python -m pip install -e .[dev]
pytest -q
caproute-screen --config configs/p0_screening.yaml --validate-only
caproute-screen --config configs/p0_screening.yaml --limit 300
```

## 예상 output

```text
outputs/p0/<run_id>/
  run_manifest.json
  predictions/<parser>.jsonl
  metrics/<parser>.json
  failures/<parser>.jsonl
cache/parsers/<fingerprint>.json
```

각 manifest에는 config hash, git commit/dirty, 환경·GPU, dataset manifest, parser version 및 실행 시간이 포함된다.

## P0 완료 조건

- Cheap와 Strong parser가 동일 `CanonicalDocument`를 반환한다.
- 같은 입력/설정의 두 번째 실행은 cache를 사용한다.
- parser별 quality, p50, p95, GPU seconds/page, peak VRAM을 출력한다.
- 실패 page는 전체 실행을 중단하지 않고 별도 저장된다.
- document/page identity와 provenance가 output에서 보존된다.
- 300~500 sample 명령이 준비되고 validate-only가 데이터/의존성 문제를 사전 검출한다.
- offline tests가 통과한다.

## 예상 failure mode

- PubTables annotation/image/PDF 경로 불일치.
- 공식 PubTables 배포는 page/table image와 XML, PDF 좌표 annotation을 제공하지만 원본 PubMed PDF 확보는 별도 단계다.
- PubTables 배포본에 원본 PDF가 없고 page image만 존재하여 native PDF parser 비교가 불가능함.
- Docling 미설치 또는 최초 model download 공간 부족.
- Windows CUDA/PyTorch 호환성. 현재 기본 Anaconda 환경의 torch native abort를 피하기 위해 P0 core는 torch를 강제 import하지 않는다.
- 매우 짧은 run에서 전력 sampling 간격보다 실행이 빨라 energy가 결측됨.
- cache fingerprint에 parser/model revision이 빠져 stale prediction이 재사용됨.
- P0 table proxy metric을 공식 GriTS로 잘못 해석할 위험.

## 구현 순서

1. scaffold/core/cache/IR
2. dataset loader
3. Cheap/Strong baseline adapters
4. evaluator/benchmark/CLI
5. offline tests와 synthetic smoke run
6. P0 Gate 보고. 실제 300~500 sample 결과 없이는 P0 Gate를 PASS로 선언하지 않는다.
