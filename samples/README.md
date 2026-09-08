# Sample corpus

Enterprise-flavored documents for the demo. Upload these via the `/upload` page or:

```
TOKEN=<paste from /api/auth/login>
for f in samples/*.md; do
  curl -H "Authorization: Bearer $TOKEN" -F "file=@$f" http://localhost:8000/api/upload/file
done
```

Files:
- `cuda-oom-runbook.md` — incident runbook (CUDA OOM under burst)
- `retention-policy.md` — data retention policy excerpt
- `payment-service-runbook.md` — retry / DLQ / idempotency reference
