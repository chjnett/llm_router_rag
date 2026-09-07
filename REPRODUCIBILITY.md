# Reproducibility Checklist

모든 실험에 아래 정보를 저장한다.

## Code

- [ ] git commit
- [ ] dirty working tree 여부
- [ ] config file
- [ ] config hash

## Environment

- [ ] OS
- [ ] Python
- [ ] CUDA
- [ ] PyTorch
- [ ] Transformers
- [ ] relevant parser library versions

## Hardware

- [ ] GPU name
- [ ] VRAM
- [ ] CPU
- [ ] RAM

## Model

- [ ] model name
- [ ] revision
- [ ] dtype
- [ ] quantization
- [ ] batch size
- [ ] decoding config

## Dataset

- [ ] dataset name
- [ ] version
- [ ] split
- [ ] document IDs
- [ ] sample count
- [ ] preprocessing version

## Randomness

- [ ] seed
- [ ] NumPy seed
- [ ] PyTorch seed
- [ ] sklearn seed

## Measurement

- [ ] warmup count
- [ ] repeated runs
- [ ] p50
- [ ] p95
- [ ] peak VRAM
- [ ] GPU seconds
- [ ] energy if available

## Output Cache

모든 parser/model raw output은 재실행 없이 재평가할 수 있게 저장한다.

