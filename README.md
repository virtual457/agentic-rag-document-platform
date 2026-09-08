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
    Production-grade RAG and agentic Q&amp;A platform that ingests enterprise documents (PDFs, DOCX, HTML, Markdown, plain-text, log files), retrieves relevant context via hybrid semantic + keyword + metadata search with cross-encoder re-ranking, and returns grounded answers with source citations. A LangGraph five-agent orchestrator (Router, Retrieval, Reasoning, Evaluator, Validation, Action) extends the pipeline with tool-calling into Jira, ServiceNow, Slack, email, HTTP webhooks, and an append-only audit log. Every LLM, embedding, vector store, and metadata store is pluggable at the environment-variable level, so the same code runs on Google Gemini + ChromaDB + MongoDB for local development or AWS Bedrock LLaMA 3 + Titan Embeddings + OpenSearch Serverless + DynamoDB for production.
    <br/>
    <a href="#architecture"><strong>Explore the Architecture »</strong></a>
    <br/><br/>
    <a href="#getting-started">Quick Start</a>
    ·
    <a href="https://github.com/chandankeelara/agentic-rag-document-platform/issues">Report Bug</a>
    ·
    <a href="#features">View Features</a>
  </p>
</div>

## Table of Contents

- [About](#about-the-project)
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

This platform indexes enterprise documents and answers natural-language questions over them with citations. It ships as a FastAPI backend + Next.js frontend that runs locally with **Google Gemini 2.5 Flash + Gemini text-embedding-004 + ChromaDB + MongoDB** in about a minute, and re-deploys to AWS with **Bedrock LLaMA 3 + Titan Embeddings + OpenSearch Serverless + DynamoDB + S3 + SQS + Step Functions + Lambda** by flipping four env vars and running `terraform apply` against the Terraform module in `infra/terraform/`.

The system is designed for the realistic enterprise mix of content: structured PDFs, semi-structured runbooks and KB articles, unstructured telemetry logs, and Markdown / HTML pages. Each content type uses a chunking strategy tuned for its shape (section-aware for docs, event-based for logs grouped by `trace_id` + timestamp window + severity) and is stored with rich per-chunk metadata so retrieval can be filtered by section, source type, product, service, environment, version, page number, and access scope.

### Highlights

- **Pluggable LLM**: Google Gemini 2.5 Flash (default) or AWS Bedrock LLaMA 3.
- **Pluggable embeddings**: Gemini `text-embedding-004` (768-dim), AWS Titan Embeddings (1536-dim), or `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fully local and free).
- **Pluggable vector store**: ChromaDB (local dev), OpenSearch Serverless (production), or PostgreSQL + pgvector.
- **Pluggable metadata store**: MongoDB (local) or DynamoDB (AWS).
- **LangGraph five-agent orchestration**: Router, Retrieval, Reasoning (ReAct), Evaluator (three rounds vs. 90 / 100 quality gate), Validation (two factuality rounds cross-checking every claim), Action.
- **Hybrid retrieval**: vector similarity + keyword search (Chroma `$contains`, OpenSearch `match`, pgvector `tsvector`) fused via Reciprocal Rank Fusion, then re-ranked by a `cross-encoder/ms-marco-MiniLM-L-6-v2` cross-encoder.
- **Tool-calling**: Jira, ServiceNow, Slack, email (SMTP), HTTPS webhooks, audit log. The Action Agent invokes them with structured Pydantic-validated arguments.
- **Hallucination mitigation**: strict grounding prompts, similarity thresholds, source citations on every answer, three evaluation rounds, and a Validation Agent that flags UNSUPPORTED claims and re-runs generation.
- **Streaming**: Server-Sent Events for the pipeline run and WebSocket for bidirectional agent Q&A (the ReAct agent can pause mid-loop with `ask_user`, wait up to 60 seconds for a reply, then resume with the user's answer folded into scratchpad state).
- **Production controls**: timeouts, exponential-backoff retries, DLQs, idempotent ingestion, four-layer caching (query embedding / retrieval / final answer / metadata).
- **Multi-tenant access control**: per-chunk `access_scope` metadata enforced at retrieval time, KMS-encrypted stores, Secrets Manager wrappers for credentials, per-user vector-store isolation.
- **Observability**: `structlog` JSON logs with trace / request / session IDs, CloudWatch metric emitter for retrieval, generation, and tool-call latency and success rate.

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

### Provider matrix (all pluggable at env-var level)

| Layer | Local default | AWS production | Others supported |
|---|---|---|---|
| LLM | Gemini 2.5 Flash | Bedrock LLaMA 3 | — |
| Embeddings | Gemini `text-embedding-004` (768) | Titan (1536) | `sentence-transformers/all-MiniLM-L6-v2` (384) |
| Vector store | ChromaDB (local persistent) | OpenSearch Serverless | PostgreSQL + pgvector |
| Metadata store | MongoDB | DynamoDB | — |
| Cache | in-memory TTL | Redis | — |

### Compute and eventing (AWS mode)

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
| **Reasoning Agent (ReAct)** | LangGraph `create_react_agent` loop with `rag_search`, `cite_source`, and `calculator` tools; can also invoke `ask_user` via WebSocket for clarification. | `src/agents/reasoning.py` |
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

1. **Synchronous** (`POST /api/upload/file` or `POST /api/upload/url`) parses, chunks, embeds, and indexes in the request. Good for local dev and small documents.
2. **Asynchronous** (S3 to SQS to Step Functions to Lambda) recommended for production. `aws s3 cp file.pdf s3://<bucket>/uploads/<tenant>/file.pdf` triggers the ingestion Lambda (`src/ingestion/s3_worker.py`), which parses, chunks, embeds, and indexes idempotently. Failures land in the DLQ after five retries.

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
- Per-chunk metadata: `source_id, source_filename, source_type, section, chunk_index, page_number, access_scope`.

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

Implementation: `src/retrieval/hybrid.py`. Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers` (`src/retrieval/reranker.py`). Cache: `src/retrieval/cache.py` (in-memory TTL or Redis, 4 layers: embedding / retrieval / answer / metadata).

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

Retrieval evaluation is tracked separately from generation evaluation:
- **Retrieval** precision, Top-K hit rate, empty-result rate, cache hit rate.
- **Generation** answer score (0-100), factuality pass / fail, per-round retries, latency, token usage.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Security and Multi-Tenancy

- **Document-level access control** every chunk carries an `access_scope` metadata field; the Retrieval Agent injects the caller's granted scopes into the filter so out-of-scope hits are never returned by the vector store (`src/security/access_scope.py`).
- **Per-user vector-store isolation** ChromaDB uses a per-tenant directory; OpenSearch / pgvector use a per-tenant index / table.
- **KMS encryption at rest** for S3, DynamoDB, OpenSearch, and Secrets Manager entries (provisioned by `infra/terraform/kms.tf`).
- **Secrets Manager** for API keys and connection strings, with a lookup layer (`src/security/secrets.py`) that falls back to env vars for local dev.
- **JWT + bcrypt** authentication (`src/auth/`).
- **IAM** service role for the Lambda worker with fine-grained S3, SQS, DynamoDB, OpenSearch, Bedrock, and Secrets Manager permissions.
- Every Action-Agent side effect writes an entry to the append-only audit log via the `write_audit_log` tool.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Tech Stack

### AI / ML
- **LLM** Google Gemini 2.5 Flash via `langchain-google-genai` (default), AWS Bedrock LLaMA 3 via `boto3` (production alternative).
- **Embeddings** Gemini `text-embedding-004` (768-dim), AWS Titan `amazon.titan-embed-text-v1` (1536-dim), or `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fully local).
- **Frameworks** LangChain 0.3+, LangGraph 0.2+ (`create_react_agent`, `StateGraph`), Pydantic 2, `structlog`.
- **Retrieval** hybrid semantic + keyword + metadata + cross-encoder rerank via `sentence-transformers` and `rank-bm25`.

### Cloud and Infrastructure (AWS mode)
- **Compute** AWS Lambda (ingestion worker), Cloud Run / EC2 / Fargate for the FastAPI backend (choose whatever suits your latency budget).
- **API** FastAPI directly, or API Gateway v2 HTTP API fronting Lambda via `mangum`.
- **Storage** S3 (raw uploads), DynamoDB (metadata + conversation state) or MongoDB.
- **Async** SQS + DLQ (ingestion event queue), Step Functions (multi-step ingestion orchestration).
- **Vector DB** OpenSearch Serverless (`aoss:APIAccessAll`), or PostgreSQL + pgvector, or ChromaDB.
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
- A running MongoDB instance (local Docker or Atlas free tier)
- One of:
  - A Google Gemini API key (fastest way to get started, get one at https://aistudio.google.com/apikey)
  - An AWS account with Bedrock access to LLaMA 3 and Titan Embeddings and a provisioned OpenSearch Serverless collection

Optional:
- Docker + Terraform 1.5+ if you want to deploy to AWS.
- Redis (for the multi-layer cache in production; local dev uses an in-memory TTL cache).

### Backend, local dev with Gemini + ChromaDB + MongoDB

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
# open .env and set at minimum:
#   GEMINI_API_KEY=your_key
#   MONGO_URI=mongodb://localhost:27017
#   JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
# leave LLM_BACKEND=gemini, VECTOR_BACKEND=chroma, METADATA_BACKEND=mongo

uvicorn main:app --reload
# API:    http://localhost:8000
# Docs:   http://localhost:8000/docs
# Health: http://localhost:8000/api/admin/health/deep
```

### Frontend

```bash
cd ../frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# Open http://localhost:3000
```

### Ingest a document

Register at `/register`, sign in, then upload from `/upload`, or from the CLI:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"you","password":"yourpassword"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/cuda-oom-runbook.md" \
  http://localhost:8000/api/upload/file

curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"What causes CUDA OOM under burst inference?"}' \
  http://localhost:8000/api/query
```

Try the SSE and WebSocket agent modes side-by-side at `/query` in the frontend.

### AWS production mode

Switch the backend to AWS providers:

```bash
# in backend/.env
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
AWS_REGION=us-east-1
```

Provision the AWS infrastructure via Terraform:

```bash
cd infra/terraform
terraform init
terraform plan -var="project=docintel" -var="region=us-east-1"
terraform apply
```

Outputs include the ingest S3 bucket, OpenSearch endpoint, DynamoDB tables, Step Functions ARN, and API Gateway endpoint.

Upload for async ingestion:

```bash
aws s3 cp samples/cuda-oom-runbook.md s3://docintel-ingest-<account>/uploads/<tenant>/cuda-oom-runbook.md
```

The S3 event fans out through SQS + Step Functions + the Lambda worker; results land in DynamoDB and OpenSearch.

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
|   |   +-- llm/                         LLM providers (Gemini, Bedrock)
|   |   +-- embeddings/                  Embedding providers (Gemini, Titan, sentence-transformers)
|   |   +-- vector_store/                Vector stores (Chroma, OpenSearch, pgvector)
|   |   +-- metadata_store/              Metadata stores (Mongo, DynamoDB)
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
- [x] Google Gemini 2.5 Flash generation with strict grounding prompts
- [x] AWS Bedrock LLaMA 3 provider (env-var swap)
- [x] Gemini + Titan + sentence-transformers embedding providers
- [x] Hybrid retrieval (vector + keyword + RRF + cross-encoder rerank) across ChromaDB, OpenSearch, and pgvector
- [x] Section-aware chunking for docs, event-based chunking for log streams
- [x] PDF / DOCX / HTML / Markdown / plain-text parsers
- [x] Tool-calling: Jira, ServiceNow, Slack, email, HTTPS webhook, audit log
- [x] Evaluator with 90/100 gate and 3-round retry
- [x] Validation Agent with per-claim faithfulness check and 2-round retry
- [x] Multi-layer caching (in-memory + Redis, 4 TTL layers)
- [x] Production controls: timeouts, exponential-backoff retries, DLQs, idempotent ingestion
- [x] `structlog` JSON logs with trace IDs; CloudWatch metric emitter
- [x] Multi-tenant per-chunk `access_scope` enforcement + KMS + Secrets Manager + IAM
- [x] Terraform for the full AWS ingestion pipeline
- [x] SSE pipeline streaming + WebSocket bidirectional agent Q&A with `ask_user`

### In Progress
- [ ] `langchain_aws.ChatBedrock` adapter so Bedrock is a first-class ReAct tool-using citizen
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
