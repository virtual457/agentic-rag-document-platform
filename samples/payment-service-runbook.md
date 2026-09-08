# Payment Service Runbook

## Retry Behavior
- Exponential backoff, base 200ms, cap 30s.
- Idempotency-Key header required on all POST /charges.
- After 5 retries, message routes to `charges-dlq` with reason code.

## DLQ Review
Oncall reviews `charges-dlq` at 10:00 UTC daily.

## Common Failure Modes
- 4xx from card network: do not retry, escalate to Fraud team.
- 5xx from card network: retry with backoff.
- Timeout: retry with same idempotency key.
