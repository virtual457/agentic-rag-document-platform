# Data Retention Policy

## Categories

| Category | Retention |
|---|---|
| Raw customer input logs | 30 days |
| Prediction logs (aggregated) | 400 days |
| PII | Not stored beyond request |
| Internal engineering logs | 90 days |
| Financial transactions | 7 years |

## Purge
S3 lifecycle rules run daily at 03:00 UTC. Failed purges alert to `#retention-alerts`.

## Right-to-Delete
30-calendar-day SLA, including snapshotted backups.
