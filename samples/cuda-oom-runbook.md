# CUDA OOM Under Burst Inference: Runbook

## Symptom
Under burst workload (>5x baseline QPS), inference services on A100 clusters throw intermittent `CUDA out of memory` errors. Failures cluster around dynamic batch sizes and long input sequences.

## Root Causes
1. Memory fragmentation from dynamic batch shapes.
2. KV-cache growth on long-context autoregressive decoding without a hard cap.
3. Multi-model residency on the same GPU without per-model memory quotas.
4. Autocast + gradient tensors leaking from a shared training + eval process.

## Immediate Mitigations
- Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- Add continuous batching (vLLM / TensorRT-LLM).
- Cap max input length at the validator.
- Route long-context requests to a dedicated replica.

## Escalation
Page ML Infra oncall in `#gpu-oncall` when OOM rate > 0.5% over any 5-minute window.
