from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.config import get_settings
from src.ingestion.parser import ParsedDocument, ParsedSection


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _detokenize(tokens: list[str]) -> str:
    return " ".join(tokens)


def _sliding_window(text: str, size: int, overlap: int) -> list[str]:
    toks = _tokenize(text)
    if len(toks) <= size:
        return [_detokenize(toks)] if toks else []
    step = max(1, size - overlap)
    out: list[str] = []
    for i in range(0, len(toks), step):
        w = toks[i : i + size]
        if not w:
            break
        out.append(_detokenize(w))
        if i + size >= len(toks):
            break
    return out


def section_aware_chunks(
    doc: ParsedDocument,
    *,
    source_id: str,
    base_metadata: dict[str, Any],
    size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    settings = get_settings()
    size = size or settings.chunk_size_tokens
    overlap = overlap or settings.chunk_overlap_tokens
    chunks: list[Chunk] = []
    counter = 0
    for section in doc.sections:
        body = section.text.strip()
        if not body:
            continue
        windows = _sliding_window(body, size, overlap)
        for w in windows:
            meta = {
                **base_metadata,
                "source_id": source_id,
                "source_filename": doc.filename,
                "source_type": doc.source_type,
                "section": section.heading,
                "chunk_index": counter,
            }
            if section.page is not None:
                meta["page_number"] = section.page
            chunks.append(Chunk(chunk_id=f"{source_id}:{counter}", text=w, metadata=meta))
            counter += 1
    return chunks


_LOG_LINE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+"
    r"(?P<level>[A-Z]+)\s+"
    r"(?P<rest>.*)"
)


def event_based_chunks(
    doc: ParsedDocument,
    *,
    source_id: str,
    base_metadata: dict[str, Any],
    window_seconds: int = 60,
    max_events_per_chunk: int = 40,
) -> list[Chunk]:
    """Group log lines into chunks by trace_id + timestamp window + severity."""
    from datetime import datetime, timedelta

    def _parse_ts(s: str) -> datetime | None:
        s = s.rstrip("Z")
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
        return None

    events: list[dict[str, Any]] = []
    for line in doc.raw_text.splitlines():
        m = _LOG_LINE.match(line)
        if not m:
            continue
        ts = _parse_ts(m.group("ts"))
        rest = m.group("rest")
        trace_match = re.search(r"trace[_-]?id[=:]\s*([a-zA-Z0-9\-]+)", rest, re.I)
        events.append(
            {
                "ts": ts,
                "level": m.group("level"),
                "trace_id": trace_match.group(1) if trace_match else None,
                "text": line,
            }
        )
    if not events:
        return section_aware_chunks(doc, source_id=source_id, base_metadata=base_metadata)

    chunks: list[Chunk] = []
    counter = 0
    events.sort(key=lambda e: (e["trace_id"] or "", e["ts"] or datetime.min))
    bucket: list[dict[str, Any]] = []
    bucket_start: datetime | None = None
    bucket_trace: str | None = None

    def _flush(bucket: list[dict[str, Any]]) -> None:
        nonlocal counter
        if not bucket:
            return
        text = "\n".join(e["text"] for e in bucket)
        severities = list({e["level"] for e in bucket})
        meta = {
            **base_metadata,
            "source_id": source_id,
            "source_filename": doc.filename,
            "source_type": "log",
            "chunk_index": counter,
            "trace_id": bucket[0].get("trace_id"),
            "severities": severities,
            "event_count": len(bucket),
        }
        chunks.append(Chunk(chunk_id=f"{source_id}:{counter}", text=text, metadata=meta))
        counter += 1

    for ev in events:
        if not bucket:
            bucket = [ev]
            bucket_start = ev["ts"]
            bucket_trace = ev["trace_id"]
            continue
        same_trace = ev["trace_id"] == bucket_trace
        within_window = bucket_start is None or (ev["ts"] and ev["ts"] - bucket_start <= timedelta(seconds=window_seconds))
        if same_trace and within_window and len(bucket) < max_events_per_chunk:
            bucket.append(ev)
        else:
            _flush(bucket)
            bucket = [ev]
            bucket_start = ev["ts"]
            bucket_trace = ev["trace_id"]
    _flush(bucket)
    return chunks


def chunk_document(
    doc: ParsedDocument,
    *,
    source_id: str,
    base_metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    base = base_metadata or {}
    if doc.source_type == "log":
        return event_based_chunks(doc, source_id=source_id, base_metadata=base)
    return section_aware_chunks(doc, source_id=source_id, base_metadata=base)
