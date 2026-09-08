[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<a id="readme-top"></a>

<!-- PROJECT TITLE -->
<div align="center">
  <h3 align="center">Cloud-Native Agentic RAG Document Processing Platform</h3>
  <p align="center">
    Production-grade RAG and agentic Q&amp;A platform that ingests enterprise documents (PDFs, DOCX, HTML, Markdown, plain-text, log files), retrieves relevant context via hybrid semantic + keyword + metadata search with cross-encoder re-ranking, and returns grounded answers with source citations. A LangGraph five-agent orchestrator (Router, Retrieval, Reasoning, Evaluator, Validation, Action) extends the pipeline with tool-calling into Jira, ServiceNow, Slack, email, HTTP webhooks, and an append-only audit log.
    <br/><br/>
    Ships in two first-class modes, selectable via environment variables:<br/>
    <strong>Prod mode</strong> — AWS Bedrock LLaMA 3 + Titan Embeddings + OpenSearch Serverless + DynamoDB + Redis, provisioned by Terraform.<br/>
    <strong>Local mode</strong> — Google Gemini 2.5 Flash + Gemini embeddings + ChromaDB + MongoDB + in-memory cache, runs on a laptop in under a minute.
    <br/><br/>
    <a href="#architecture"><strong>Explore the Architecture »</strong></a>
    <br/><br/>
    <a href="#getting-started">Quick Start</a>
    ·
    <a href="https://github.com/chandankeelara/agentic-rag-document-platform/issues">Report Bug</a>
    ·
    <a href="#roadmap">Roadmap</a>
  </p>
</div>

## Table of Contents

- [About](#about-the-project)
- [Two Modes: Prod and Local](#two-modes-prod-and-local)
- [Architecture](#architecture)
- [Agentic Workflow](#agentic-workflow)
- [Ingestion Pipeline](#ingestion-pipeline)
- [Hybrid Retrieval](#hybrid-retrieval)
- [Hallucination Mitigation](#hallucination-mitigation)
- [Reliability and Production Controls](#reliability-and-production-controls)
- [Observability](#observability)
- [Security and Multi-Tenancy](#security-and-multi-tenancy)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contact](#contact)

## About The Project

This platform indexes enterprise documents and answers natural-language questions over them with citations. It ships as a FastAPI backend + Next.js frontend that boots into either a fully local mode (Gemini + ChromaDB + MongoDB) for laptop development or a fully AWS-native mode (Bedrock + Titan + OpenSearch Serverless + DynamoDB) for production, with the two chosen by a handful of `*_BACKEND` environment variables. Every provider is behind a Protocol interface (`LLMProvider`, `EmbeddingProvider`, `VectorStore`, `MetadataStore`), so the LangGraph orchestrator, hybrid retriever, and ingestion pipeline are backend-agnostic.

The system is designed for the realistic enterprise mix of content: structured PDFs, semi-structured runbooks and KB articles, unstructured telemetry logs, and Markdown / HTML pages. Each content type uses a chunking strategy tuned for its shape (section-aware for docs, event-based for logs grouped by `trace_id` + timestamp window + severity) and is stored with rich per-chunk metadata so retrieval can be filtered by section, source type, product, service, environment, version, page number, and access scope.

### Highlights

- **Two first-class deployment modes**: AWS Bedrock production and fully-local Gemini + ChromaDB dev, sharing 100% of the application code.
- **LangGraph five-agent orchestration**: Router, Retrieval, Reasoning (ReAct), Evaluator (three rounds vs. 90 / 100 quality gate), Validation (two factuality rounds cross-checking every claim), Action.
- **Hybrid retrieval**: vector similarity + keyword search fused via Reciprocal Rank Fusion, then re-ranked by a `cross-encoder/ms-marco-MiniLM-L-6-v2` cross-encoder.
- **Tool-calling**: Jira, ServiceNow, Slack, email (SMTP), HTTPS webhooks, audit log. The Action Agent invokes them with structured Pydantic-validated arguments.
- **Hallucination mitigation**: strict grounding prompts, source citations, three evaluation rounds, and a Validation Agent that flags UNSUPPORTED claims and re-runs generation.
- **Streaming**: Server-Sent Events with human-readable pipeline labels, plus WebSocket for bidirectional agent Q&A where the ReAct agent can pause mid-loop with `ask_user`, wait up to 60 seconds, then resume with the reply folded into scratchpad state.
- **Production controls**: timeouts, exponential-backoff retries, DLQs, idempotent ingestion, four-layer caching (query embedding / retrieval / final answer / metadata).
- **Multi-tenant access control**: per-chunk `access_scope` metadata enforced at retrieval time, KMS-encrypted stores, Secrets Manager wrappers for credentials, per-tenant vector-store isolation.
- **Observability**: `structlog` JSON logs with trace / request / session IDs, CloudWatch metric emitter for retrieval, generation, and tool-call latency and success rate.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Two Modes: Prod and Local

Both modes share the same application code. Switch between them by editing four env vars.

### Prod mode (AWS-native, default)

| Layer | Provider |
|---|---|
| LLM | AWS Bedrock LLaMA 3 (`meta.llama3-70b-instruct-v1:0`) via `langchain_aws.ChatBedrockConverse` |
| Embeddings | AWS Titan `amazon.titan-embed-text-v1` (1536-dim) |
| Vector store | OpenSearch Serverless (VECTORSEARCH collection, KMS-encrypted) |
| Metadata store | DynamoDB (metadata + sessions tables, TTL, on-demand billing) |
| Cache | Redis |
| Ingestion event bus | S3 → SQS + DLQ → Step Functions → Lambda |
| Secrets | AWS Secrets Manager (encrypted with a per-project KMS key) |
| Observability | CloudWatch structured JSON logs + `PutMetricData` |
| IaC | Terraform in `infra/terraform/` (KMS, S3, SQS, DynamoDB, OpenSearch, Secrets Manager, IAM, Lambda, Step Functions, API Gateway v2) |

```env
LLM_BACKEND=bedrock
EMBEDDINGS_BACKEND=titan
VECTOR_BACKEND=opensearch
METADATA_BACKEND=dynamodb
CACHE_BACKEND=redis

BEDROCK_MODEL_ID=meta.llama3-70b-instruct-v1:0
BEDROCK_REGION=us-east-1
OPENSEARCH_ENDPOINT=https://<collection-id>.us-east-1.aoss.amazonaws.com
DYNAMODB_TABLE_METADATA=docintel-metadata
DYNAMODB_TABLE_SESSIONS=docintel-sessions
REDIS_URL=redis://your-elasticache-endpoint:6379/0
AWS_REGION=us-east-1
```

### Local mode (laptop dev, no AWS bill)

| Layer | Provider |
|---|---|
| LLM | Google Gemini 2.5 Flash via `langchain-google-genai` |
| Embeddings | Gemini `text-embedding-004` (768-dim), or `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fully offline) |
| Vector store | ChromaDB (persistent client, per-tenant directory) |
| Metadata store | MongoDB (Atlas free tier or local Docker) |
| Cache | In-memory `cachetools.TTLCache` |
| Ingestion | Synchronous, in-process (no S3 / SQS / Step Functions) |
| Secrets | `.env` file |
| Observability | `structlog` JSON to stdout |

```env
LLM_BACKEND=gemini
EMBEDDINGS_BACKEND=gemini
VECTOR_BACKEND=chroma
METADATA_BACKEND=mongo
CACHE_BACKEND=memory

GEMINI_API_KEY=your_key
MONGO_URI=mongodb://localhost:27017
```

### Mix and match

Every provider is independent. You can, for example, run **Local LLM + Prod vector store** to iterate on the graph while querying a real OpenSearch index (`LLM_BACKEND=gemini, VECTOR_BACKEND=opensearch`), or **Prod LLM + Local vector store** to test Bedrock prompting against a small local Chroma index (`LLM_BACKEND=bedrock, VECTOR_BACKEND=chroma`).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Architecture

```
+-----------------------------------------------------------+
|                        Web Client                          |
|             Next.js 15 + React 19 + TypeScript             |
|          /dashboard  /upload  /query  /history             |
+---------+----------------------+----------+----------------+
          | HTTPS                | SSE      | WebSocket
          v                      v          v
+-----------------------------------------------------------+
|                  FastAPI (backend/main.py)                |
|   /api/auth   /api/upload   /api/query   /api/agent/ws    |
|   /api/admin  (JWT + bcrypt, per-request middleware)      |
+---------+-----------------+---------------+---------------+
          |                 |               |
          v                 v               v
+-------------------+  +-----------+   +-------------------+
| LangGraph Agent   |  | Ingestion |   | Sessions          |
| Orchestrator      |  | Pipeline  |   | (60s question,    |
|  Router           |  | parse ->  |   |  5-min lifecycle) |
|  Retrieval Agent  |  | chunk ->  |   +-------------------+
|  Reasoning (ReAct)|  | embed ->  |
|  Evaluator (3x)   |  | index     |
|  Validation (2x)  |  +-----------+
|  Action Agent     |
+---+-----+-----+---+
    |     |     |
    v     v     v
Vector  Metadata  Tools
Store   Store    (Jira, ServiceNow, Slack,
                 email, http_webhook, audit_log)
```

### Compute and eventing (Prod mode)

```
Document Upload  ->  S3 Bucket (KMS-encrypted, versioned)
                          |
                          v
                     SQS Event Queue (DLQ + max 5 retries)
                          |
                          v
                     Step Functions state machine
                          |
                          v
             Lambda ingestion worker (src/ingestion/s3_worker.py)
                          |
                          v
       parse -> chunk -> embed (Titan) -> index (OpenSearch)
```

Provisioned by Terraform in `infra/terraform/` (S3, SQS + DLQ, Step Functions, Lambda + IAM policy, OpenSearch Serverless collection, DynamoDB tables, KMS key, Secrets Manager entries, API Gateway HTTP API).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Agentic Workflow

LangGraph orchestrates a directed graph of specialized agents. Each agent has a clear responsibility, structured outputs, and traceable Thought, Action, Observation steps.

| Agent | Responsibility | Code |
|---|---|---|
| **Query Router** | Classifies the user query as `qa` (factual grounded answer), `action` (external side effect requested), or `unclear` (short-circuit). | `src/agents/router.py` |
| **Retrieval Agent** | Hybrid semantic + keyword search with metadata filtering and access-scope enforcement, returns Top-K 3-5 chunks with citations. | `src/agents/retrieval_agent.py` |
| **Reasoning Agent (ReAct)** | LangGraph `create_react_agent` loop with `rag_search`, `cite_source`, and `calculator` tools; can also invoke `ask_user` via WebSocket for clarification. Works with either Gemini or Bedrock LLM via a unified LangChain adapter. | `src/agents/reasoning.py` |
| **Evaluator** | Two-part score (35 pts keyword coverage + 65 pts LLM rubric) against a 90 / 100 quality gate. Re-runs the Reasoning Agent up to three rounds if the gate is not met. | `src/agents/evaluator.py` |
| **Validation Agent** | Enumerates every atomic claim in the draft answer and marks each SUPPORTED or UNSUPPORTED against the retrieved chunks. Up to two rounds; on failure, re-runs Reasoning. | `src/agents/validation.py` |
| **Action Agent** | When the query implies a side effect, invokes the appropriate tool (Jira, ServiceNow, Slack, email, HTTP webhook) with structured Pydantic arguments and writes an audit-log entry. | `src/agents/action.py` |

### Why ReAct here

- Tool-driven reasoning beats single-shot LLM guessing for enterprise knowledge.
- Iterative refinement plus the Evaluator's quality gate reduces first-pass hallucinations.
- Thought, Action, Observation traces are persisted per request as `reasoning_trace`, making audits and debugging straightforward.
- The Validation Agent enforces grounded-answer-only as a hard gate before the Action Agent is allowed to run.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Ingestion Pipeline

```
Document Upload  ->  Parse  ->  Chunk  ->  Embed  ->  Store
```

Two ingestion modes:

1. **Synchronous** (`POST /api/upload/file` or `POST /api/upload/url`) parses, chunks, embeds, and indexes in the request. Default in Local mode. Also works in Prod mode for one-off uploads. Accepts free-form business metadata via a `metadata` form field (JSON), e.g. `{"product":"payments","version":"v2.3.1","severity":"high","access_scope":"engineering"}`, which is stamped onto every chunk.
2. **Asynchronous** (S3 to SQS to Step Functions to Lambda). Prod mode default. `aws s3 cp file.pdf s3://<bucket>/uploads/<tenant>/file.pdf` triggers the ingestion Lambda (`src/ingestion/s3_worker.py`), which parses, chunks, embeds, and indexes idempotently. Failures land in the DLQ after five retries.

### Parsers (`src/ingestion/parser.py`)
- **PDF** pypdf per-page, with lightweight section detection for numbered / uppercase headings and page-number metadata.
- **DOCX** python-docx paragraph-level, using Word `Heading 1..3` and `Title` styles to break sections.
- **HTML** BeautifulSoup with `<script> <style> <nav> <footer>` removed, `<h1..h4>` used as section boundaries.
- **Markdown** split on `#` headings.
- **Plain text** heuristic detection of numeric and all-caps section titles.
- **Log files** treated as event streams (see below).

### Chunking (`src/ingestion/chunker.py`)

**Section-aware chunking** for docs and knowledge articles:
- Chunk size 500 tokens, overlap 50 tokens (configurable via `.env`).
- Per-chunk metadata: `source_id, source_filename, source_type, section, chunk_index, page_number, access_scope`, plus any business metadata passed at upload.

**Event-based chunking** for logs:
- Parse each line into `(timestamp, level, trace_id, text)`.
- Group by `trace_id` first, then break every 60-second window or 40 events (whichever is smaller).
- Metadata per chunk includes `trace_id, severities, event_count`.

### Per-chunk metadata example

```json
{
  "source_id": "b8f0c1...",
  "source_filename": "payment-runbook.pdf",
  "source_type": "pdf",
  "section": "Retry Failure Handling",
  "chunk_index": 8,
  "page_number": 12,
  "product": "payments",
  "service": "payment-api",
  "environment": "production",
  "version": "v2.3.1",
  "severity": "high",
  "access_scope": "engineering"
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Hybrid Retrieval

Vector search captures semantic meaning; keyword search ensures exact-match for identifiers (error codes like `ERR_502`, service names, version strings, API names); metadata filters narrow the candidate set by service, environment, version, and access scope. All three signals are merged via Reciprocal Rank Fusion and re-ranked by a cross-encoder.

```
Query  ->  Embed  ->  Vector Top-3K
                           |
Query  ->  Tokenize  ->  Keyword Top-3K
                           +---> RRF merge  ->  cross-encoder rerank  ->  Top 3-5
Filters (svc, env, scope) -+
```

Implementation: `src/retrieval/hybrid.py`. Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers` (`src/retrieval/reranker.py`). Cache: `src/retrieval/cache.py` (Redis in Prod, in-memory TTL in Local; 4 layers: embedding / retrieval / answer / metadata).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Hallucination Mitigation

- Strict system prompts that answer only from retrieved context; explicit "not enough context" refusal.
- Similarity thresholds and metadata filters on retrieval.
- Source citations on every answer (`source_id`, filename, chunk index, reasoning).
- Cross-encoder re-rank before generation.
- **Evaluator** re-runs generation up to three rounds if the 90 / 100 quality gate is not met.
- **Validation Agent** enumerates every atomic claim as SUPPORTED / UNSUPPORTED against retrieved chunks and re-runs generation on any UNSUPPORTED claim (up to two factuality rounds).
- Full RAG trace persisted per request: query, retrieved chunk IDs, per-round scores, reasoning trace, validation verdict, actions taken, and latency.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Reliability and Production Controls

| Failure mode | Control |
|---|---|
| Parse errors, unsupported doc types | Per-type parser, fallback to raw-text parser |
| Embedding API failures | Retries with exponential backoff (`tenacity`) |
| Vector DB write failures | Idempotent upserts keyed on `chunk_id = source_id:index` |
| Bedrock / Gemini timeouts | Timeouts, retries, tenant-side throttling |
| Low-confidence retrieval | Refuse with "not enough context" instead of guessing |
| Tool-call failures | Wrapped errors, string-returned failure reason, audit-log entry |
| Repeat ingestion | Idempotent keys on S3 object to chunk ID, upsert semantics |
| Reasoning loop divergence | Hard cap on eval rounds + validation rounds |

Multi-layer caching (`src/retrieval/cache.py`) reduces tail latency:
- **Query embedding cache** (24h TTL)
- **Top-K retrieval cache** (5 min TTL)
- **Final-answer cache** (10 min TTL, opt-in for stable knowledge)
- **Metadata cache** (1h TTL)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Observability

Every request logs (via `structlog` JSON in `src/observability/logger.py`): user tenant, query, retrieved chunk IDs, per-round scores, prompt version, model response, latency (retrieval, generation, validation), token usage, tool-call success rate, and error info with `trace_id`. Surfaced via CloudWatch metric emissions (`src/observability/metrics.py`) with the `MetricsEmitter.emit()` and `timed()` context manager.

SSE events include a human-readable `label` field so the frontend can show a live pipeline (`Routing query as qa...`, `Searching documents... found 5 relevant chunks`, `Reasoning complete (7 steps)`, `Evaluation round 1: 92/100 (passed gate)`, `Validating claims... 6 supported, 0 unsupported (grounded)`, `Actions completed (2 tool calls, audit log written)`).

Retrieval evaluation is tracked separately from generation evaluation:
- **Retrieval** precision, Top-K hit rate, empty-result rate, cache hit rate.
- **Generation** answer score (0-100), factuality pass / fail, per-round retries, latency, token usage.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Security and Multi-Tenancy

- **Document-level access control** every chunk carries an `access_scope` metadata field; the Retrieval Agent injects the caller's granted scopes into the filter so out-of-scope hits are never returned by the vector store (`src/security/access_scope.py`).
- **Per-tenant vector-store isolation** ChromaDB uses a per-tenant directory; OpenSearch / pgvector use a per-tenant index / table.
- **KMS encryption at rest** for S3, DynamoDB, OpenSearch, and Secrets Manager entries (provisioned by `infra/terraform/kms.tf`).
- **Secrets Manager** for API keys and connection strings, with a lookup layer (`src/security/secrets.py`) that falls back to env vars for local dev.
- **JWT + bcrypt** authentication (`src/auth/`).
- **IAM** service role for the Lambda worker with fine-grained S3, SQS, DynamoDB, OpenSearch, Bedrock, and Secrets Manager permissions.
- Every Action-Agent side effect writes an entry to the append-only audit log via the `write_audit_log` tool.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Tech Stack

### AI / ML
- **LLM** AWS Bedrock LLaMA 3 via `langchain-aws` (Prod default), Google Gemini 2.5 Flash via `langchain-google-genai` (Local default).
- **Embeddings** AWS Titan `amazon.titan-embed-text-v1` (Prod), Gemini `text-embedding-004` (Local), `sentence-transformers/all-MiniLM-L6-v2` (fully offline).
- **Frameworks** LangChain 0.3+, LangGraph 0.2+ (`create_react_agent`, `StateGraph`), Pydantic 2, `structlog`.
- **Retrieval** hybrid semantic + keyword + metadata + cross-encoder rerank via `sentence-transformers` and `rank-bm25`.

### Cloud and Infrastructure (Prod mode)
- **Compute** AWS Lambda (ingestion worker), Cloud Run / EC2 / Fargate for the FastAPI backend.
- **API** FastAPI directly, or API Gateway v2 HTTP API fronting Lambda via `mangum`.
- **Storage** S3 (raw uploads), DynamoDB (metadata + conversation state).
- **Async** SQS + DLQ (ingestion event queue), Step Functions (multi-step ingestion orchestration).
- **Vector DB** OpenSearch Serverless (`aoss:APIAccessAll`).
- **Cache** Redis (ElastiCache or self-hosted).
- **Observability** CloudWatch logs and metrics, structured JSON logs, trace IDs, request IDs.
- **IaC** Terraform (`infra/terraform/`), one file per AWS resource type.
- **Security** IAM, KMS, Secrets Manager.

### Backend
- **Language** Python 3.11+ (typed with `pydantic-settings` for env parsing).
- **Framework** FastAPI 0.115 with SSE via `sse-starlette` and native WebSocket support.
- **Reliability** timeouts, `tenacity` retries with exponential backoff, DLQs (SQS), idempotent ingestion, four-layer caching, singleton clients.

### Frontend
- **Framework** Next.js 15 (App Router) + React 19 + TypeScript.
- **Auth** JWT held in a React context; forwarded via `Authorization: Bearer` header, or via query-string `?token=` on SSE / WebSocket endpoints (browsers cannot set headers on those).
- **Pages** `/dashboard`, `/upload`, `/query` (SSE + WebSocket modes), `/history`, `/login`, `/register`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

- Python 3.11+
- Node 20+
- Either:
  - **For Local mode**: a Google Gemini API key (https://aistudio.google.com/apikey) and a MongoDB instance (local Docker or Atlas free tier).
  - **For Prod mode**: an AWS account with Bedrock access to `meta.llama3-70b-instruct-v1:0` and `amazon.titan-embed-text-v1`, and Terraform 1.5+ to provision the rest.

### Local mode quick start (fastest path to a working demo)

```bash
git clone https://github.com/chandankeelara/agentic-rag-document-platform.git
cd agentic-rag-document-platform/backend

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# In .env, override the Prod defaults with Local mode:
#   LLM_BACKEND=gemini
#   EMBEDDINGS_BACKEND=gemini
#   VECTOR_BACKEND=chroma
#   METADATA_BACKEND=mongo
#   CACHE_BACKEND=memory
#   GEMINI_API_KEY=your_key
#   MONGO_URI=mongodb://localhost:27017
#   JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

uvicorn main:app --reload
```

Frontend:

```bash
cd ../frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# http://localhost:3000
```

Ingest a sample and query it:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"you","password":"yourpassword"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/cuda-oom-runbook.md" \
  -F 'metadata={"product":"gpu-infra","severity":"high","access_scope":"engineering"}' \
  http://localhost:8000/api/upload/file

curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"What causes CUDA OOM under burst inference?"}' \
  http://localhost:8000/api/query
```

### Prod mode quick start (AWS-native)

**1. Provision AWS infra with Terraform.**

```bash
cd infra/terraform
terraform init
terraform apply -var="project=docintel" -var="region=us-east-1"
# outputs: ingest_bucket, opensearch_endpoint, metadata_table,
# sessions_table, sfn_state_machine_arn, query_api_endpoint, kms_key_arn
```

**2. Populate Secrets Manager** with `docintel/jwt-secret`, `docintel/bedrock-model-id`, and (optional) `docintel/jira-api-token`, `docintel/servicenow-password`, `docintel/slack-webhook-url`, `docintel/smtp-password`.

**3. Backend `.env`** (Prod defaults, so `cp .env.example .env` gets you 90% of the way):

```env
LLM_BACKEND=bedrock
EMBEDDINGS_BACKEND=titan
VECTOR_BACKEND=opensearch
METADATA_BACKEND=dynamodb
CACHE_BACKEND=redis

BEDROCK_MODEL_ID=meta.llama3-70b-instruct-v1:0
BEDROCK_REGION=us-east-1
OPENSEARCH_ENDPOINT=<terraform output opensearch_endpoint>
DYNAMODB_TABLE_METADATA=docintel-metadata
DYNAMODB_TABLE_SESSIONS=docintel-sessions
REDIS_URL=redis://<your-elasticache>:6379/0
AWS_REGION=us-east-1
```

**4. Upload documents via S3** (fans out through SQS + Step Functions + Lambda):

```bash
aws s3 cp samples/cuda-oom-runbook.md s3://docintel-ingest-<account>/uploads/<tenant>/cuda-oom-runbook.md
```

**5. Deploy the FastAPI backend** to Cloud Run, Fargate, or EC2 with the `.env` above and appropriate IAM. The frontend can be built and served from any static host (S3 + CloudFront, Vercel, or Cloud Run).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

```
agentic-rag-document-platform/
|
+-- backend/
|   +-- main.py                          FastAPI entry point, route registration, lifespan
|   +-- requirements.txt
|   +-- .env.example                     Full env matrix (server, auth, all providers, tools, AWS)
|   +-- api/                             HTTP routes
|   |   +-- auth_routes.py
|   |   +-- upload_routes.py             POST /api/upload/{file,url} + list + delete
|   |   +-- query_routes.py              POST /api/query, GET /api/query/stream (SSE), history
|   |   +-- agent_ws_routes.py           WebSocket /api/agent/ws with bidirectional Q&A
|   |   +-- admin_routes.py              stats, deep health check
|   +-- src/
|   |   +-- config.py                    pydantic-settings, single source of truth for env
|   |   +-- session.py                   Agent session registry (60s question / 5min lifecycle)
|   |   +-- llm/                         LLM providers (Bedrock, Gemini)
|   |   +-- embeddings/                  Embedding providers (Titan, Gemini, sentence-transformers)
|   |   +-- vector_store/                Vector stores (OpenSearch, Chroma, pgvector)
|   |   +-- metadata_store/              Metadata stores (DynamoDB, Mongo)
|   |   +-- ingestion/
|   |   |   +-- parser.py                PDF / DOCX / HTML / MD / TXT / logs
|   |   |   +-- chunker.py               Section-aware + event-based
|   |   |   +-- pipeline.py              Synchronous ingest pipeline
|   |   |   +-- s3_worker.py             AWS Lambda handler for S3 -> SQS -> Step Fn
|   |   +-- retrieval/
|   |   |   +-- hybrid.py                Vector + keyword + RRF + rerank
|   |   |   +-- reranker.py              ms-marco-MiniLM-L-6-v2 cross-encoder
|   |   |   +-- cache.py                 In-memory + Redis, 4 TTL layers
|   |   +-- agents/                      LangGraph 5-agent orchestrator
|   |   |   +-- state.py                 AgentState TypedDict
|   |   |   +-- router.py
|   |   |   +-- retrieval_agent.py
|   |   |   +-- reasoning.py             create_react_agent + rag_search / cite / calc / ask_user
|   |   |   +-- evaluator.py             35 keyword + 65 LLM, 3-round retry vs 90/100 gate
|   |   |   +-- validation.py            SUPPORTED / UNSUPPORTED per-claim, 2-round retry
|   |   |   +-- action.py                Jira / ServiceNow / Slack / email / webhook / audit
|   |   |   +-- orchestrator.py          StateGraph with conditional edges + astream
|   |   +-- tools/                       LangChain StructuredTools
|   |   |   +-- rag_search.py
|   |   |   +-- citation.py
|   |   |   +-- calculator.py
|   |   |   +-- ask_user.py              WebSocket-blocking, 60s timeout
|   |   |   +-- jira.py                  REST v3 with Basic auth
|   |   |   +-- servicenow.py            Table API incident
|   |   |   +-- slack.py                 Incoming webhook
|   |   |   +-- email_tool.py            SMTP + STARTTLS
|   |   |   +-- http_webhook.py          Generic HTTPS webhook
|   |   |   +-- audit_log.py             Persists to metadata store
|   |   |   +-- registry.py              build_qa_tools() and build_action_tools()
|   |   +-- observability/
|   |   |   +-- logger.py                structlog JSON + ContextVars
|   |   |   +-- metrics.py               CloudWatch emitter + timed() context manager
|   |   +-- security/
|   |   |   +-- access_scope.py          Per-chunk scope enforcement
|   |   |   +-- secrets.py               Secrets Manager wrapper with env fallback
|   |   +-- auth/                        JWT + bcrypt + MongoDB user store
|
+-- frontend/
|   +-- app/
|   |   +-- dashboard/page.tsx           Stats, backends, quick links
|   |   +-- upload/page.tsx              File + URL ingest, source list, delete
|   |   +-- query/page.tsx               SSE and WebSocket agent modes side-by-side
|   |   +-- history/page.tsx             Past outputs with score + route
|   |   +-- login/, register/, layout.tsx, page.tsx, globals.css
|   +-- contexts/AuthContext.tsx         JWT storage + hooks
|   +-- next.config.js, package.json, tsconfig.json, tailwind.config.js
|
+-- infra/
|   +-- terraform/                       AWS infrastructure (S3, SQS, Step Functions, Lambda,
|   |                                    DynamoDB, OpenSearch Serverless, KMS, Secrets Manager,
|   |                                    IAM, API Gateway v2)
|   +-- lambda_stub/                     Placeholder handler until real container image is built
|
+-- samples/                             Small enterprise-flavored corpus for the demo
+-- README.md
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

### Shipped
- [x] LangGraph five-agent orchestrator (Router, Retrieval, Reasoning, Evaluator, Validation, Action)
- [x] AWS Bedrock LLaMA 3 via `langchain-aws` (Prod default, first-class ReAct tool-use)
- [x] Google Gemini 2.5 Flash (Local default)
- [x] AWS Titan + Gemini + sentence-transformers embedding providers
- [x] Hybrid retrieval (vector + keyword + RRF + cross-encoder rerank) across ChromaDB, OpenSearch, and pgvector
- [x] Section-aware chunking for docs, event-based chunking for log streams
- [x] PDF / DOCX / HTML / Markdown / plain-text parsers
- [x] Free-form business metadata (product / version / severity / etc.) at upload time, stamped onto every chunk
- [x] Tool-calling: Jira, ServiceNow, Slack, email, HTTPS webhook, audit log
- [x] Evaluator with 90/100 gate and 3-round retry
- [x] Validation Agent with per-claim faithfulness check and 2-round retry
- [x] Multi-layer caching (in-memory + Redis, 4 TTL layers)
- [x] Production controls: timeouts, exponential-backoff retries, DLQs, idempotent ingestion
- [x] `structlog` JSON logs with trace IDs; CloudWatch metric emitter
- [x] Multi-tenant per-chunk `access_scope` enforcement + KMS + Secrets Manager + IAM
- [x] Terraform for the full AWS ingestion pipeline
- [x] SSE pipeline streaming with human-readable labels + WebSocket bidirectional agent Q&A with `ask_user`

### In Progress
- [ ] LangGraph checkpointer (DynamoDB in Prod / Mongo in Local) for multi-turn conversation memory
- [ ] Streaming responses end-to-end (LLM token stream to API to client)
- [ ] Eval harness with retrieval and generation metric dashboards

### Planned
- [ ] Cross-document reasoning (multi-hop retrieval with query decomposition)
- [ ] Agentic auto-RCA from telemetry log clusters
- [ ] Per-tenant prompt customization + prompt registry
- [ ] On-call assistant integrations (PagerDuty, Opsgenie)
- [ ] Container-image Lambda deployment for the ingestion worker (heavy deps: pypdf, sentence-transformers)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

**Chandan Gowda K S**

- gowdakeelarashivan.c@northeastern.edu
- [LinkedIn](https://www.linkedin.com/in/chandan-gowda-k-s-765194186/)
- [GitHub @chandankeelara](https://github.com/chandankeelara)
- [Portfolio](https://chandankeelara.github.io)

**Project Link**: [github.com/chandankeelara/agentic-rag-document-platform](https://github.com/chandankeelara/agentic-rag-document-platform)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS -->
[contributors-shield]: https://img.shields.io/github/contributors/chandankeelara/agentic-rag-document-platform.svg?style=for-the-badge
[forks-shield]: https://img.shields.io/github/forks/chandankeelara/agentic-rag-document-platform.svg?style=for-the-badge
[stars-shield]: https://img.shields.io/github/stars/chandankeelara/agentic-rag-document-platform.svg?style=for-the-badge
[issues-shield]: https://img.shields.io/github/issues/chandankeelara/agentic-rag-document-platform.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/chandankeelara/agentic-rag-document-platform.svg?style=for-the-badge
[contributors-url]: https://github.com/chandankeelara/agentic-rag-document-platform/graphs/contributors
[forks-url]: https://github.com/chandankeelara/agentic-rag-document-platform/network/members
[stars-url]: https://github.com/chandankeelara/agentic-rag-document-platform/stargazers
[issues-url]: https://github.com/chandankeelara/agentic-rag-document-platform/issues
[license-url]: https://github.com/chandankeelara/agentic-rag-document-platform/blob/main/LICENSE
