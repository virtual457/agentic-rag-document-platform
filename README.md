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
    Production-grade RAG and agentic Q&amp;A platform that ingests enterprise documents (PDFs, runbooks, knowledge articles, telemetry logs, support docs), retrieves relevant context via hybrid semantic + keyword + metadata search, and returns grounded answers with source citations using AWS Bedrock LLaMA 3, extended into a multi-agent system (Router → Retrieval → Reasoning → Validation → Action) via LangChain + LangGraph with tool-calling to Jira, ServiceNow, email, and audit logging.
    <br/>
    <a href="#architecture"><strong>Explore the Architecture »</strong></a>
    <br/><br/>
    <a href="#getting-started">Quick Start</a>
    ·
    <a href="https://github.com/virtual457/agentic-rag-document-platform/issues">Report Bug</a>
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

This platform indexes enterprise documents and answers natural-language questions over them with citations. It runs serverless on AWS, uses **AWS Bedrock with LLaMA 3** for generation and **AWS Titan Embeddings** (768-dim) for retrieval, and is extended with a **LangGraph** multi-agent workflow that can not only answer but also act — opening Jira tickets, raising ServiceNow incidents, sending email, and writing audit log entries.

The system is designed for the realistic enterprise mix of content: structured PDFs, semi-structured runbooks and KB articles, unstructured telemetry logs, and database records. Each content type uses a chunking strategy tuned for its shape (section-aware for docs, event-based for logs) and is stored with rich per-chunk metadata so retrieval can be filtered by service, environment, version, document type, and access scope.

### Highlights

- **AWS Bedrock + LLaMA 3** for grounded generation, with strict prompts that refuse to answer outside retrieved context.
- **Hybrid retrieval**: semantic vector search + keyword exact-match + metadata filtering + re-ranking.
- **LangGraph multi-agent orchestration**: Query Router → Retrieval → Reasoning (ReAct) → Validation → Action.
- **Tool-calling**: Jira, ServiceNow, email, audit logging — agent can act on grounded answers.
- **Hallucination mitigation**: similarity thresholds, source citations on every answer, Validation Agent that checks faithfulness against retrieved chunks.
- **Production controls**: timeouts, retries with backoff, dead-letter queues, idempotent ingestion, multi-layer caching, structured logs.
- **Multi-tenant access control**: per-chunk `access_scope` metadata + IAM service permissions + KMS encryption + Secrets Manager.
- **Indexed scale**: 1,000+ internal documents and knowledge sources, ~30% reduction in manual troubleshooting time on internal pilots.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              CLIENT                                  │
│                       (Web UI / API consumers)                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼──────────────────────────────────────┐
│                     API Gateway + FastAPI                            │
│            Auth, request validation, rate limiting                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    LangGraph Agent Orchestrator                      │
│                                                                      │
│   Query Router ──▶ Retrieval Agent ──▶ Reasoning Agent (ReAct)      │
│                                                  │                   │
│                                                  ▼                   │
│                          Validation Agent ──▶ Action Agent           │
│                                                                      │
└──┬────────────────┬─────────────────┬─────────────────┬─────────────┘
   │                │                 │                 │
   ▼                ▼                 ▼                 ▼
AWS Bedrock    OpenSearch /      DynamoDB /       Tools:
(LLaMA 3)      pgvector          Postgres         Jira, ServiceNow,
               (vectors)         (metadata,       email, audit log
                                  conv state)
```

### Compute and Eventing

```
Document Upload  ──▶  S3 Bucket  ──▶  SQS Event Queue  ──▶  Step Functions
                                                                    │
                                                                    ▼
                                                        Lambda Ingestion Worker
                                                          (parse → chunk →
                                                           embed → index)
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Agentic Workflow

LangGraph orchestrates a directed graph of specialized agents. Each agent has a clear responsibility, structured outputs, and traceable Thought → Action → Observation steps.

| Agent | Responsibility |
|---|---|
| **Query Router** | Classifies the user query (factual lookup vs. multi-step reasoning vs. action-required) and routes it to the right downstream path. |
| **Retrieval Agent** | Embeds the query, runs hybrid search (vector + keyword + metadata filter) against the vector store, applies re-ranking, returns Top-K 3–5 chunks with citations. |
| **Reasoning Agent (ReAct)** | Iteratively reasons over retrieved chunks, can call follow-up retrievals if context is insufficient, produces a grounded draft answer with citations. |
| **Validation Agent** | Verifies the draft answer's claims against retrieved chunks. Flags unsupported claims and triggers re-retrieval or refusal ("not enough context"). |
| **Action Agent** | When the query implies an action ("open a Jira ticket for…", "raise an incident…"), invokes the appropriate tool with structured arguments and writes an audit log entry. |

### Why ReAct here

- Tool-driven reasoning beats single-shot LLM guessing for enterprise knowledge.
- Iterative refinement reduces first-pass hallucinations.
- Thought → Action → Observation traces are preserved per request, making audits and debugging straightforward.
- Validation Agent enforces grounded-answer-only as a hard gate.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Ingestion Pipeline

```
Document Upload  →  S3  →  SQS  →  Step Functions  →  Lambda
   →  Parse + Clean
   →  Chunk (section-aware for docs, event-based for logs)
   →  Generate Embeddings (Titan or Sentence Transformers)
   →  Store Vectors (OpenSearch / pgvector)
   →  Store Metadata (DynamoDB / Postgres)
```

### Chunking strategies

**Documents and knowledge articles** — section-aware semantic chunking that splits on headings while preserving numbered steps and tables.
- Chunk size: **300–700 tokens**
- Overlap: **50–100 tokens**
- Per-chunk metadata stored

**Telemetry logs** — event-based chunking grouping by trace ID, request ID, service, timestamp window, error code, deployment version, environment, and severity.

### Per-chunk metadata (example)

```json
{
  "chunk_id": "doc_123_chunk_008",
  "document_id": "doc_123",
  "source": "s3://internal-docs/service-runbook.pdf",
  "title": "Payment Service Runbook",
  "section": "Retry Failure Handling",
  "product": "Payments",
  "service": "payment-api",
  "environment": "production",
  "version": "v2.3.1",
  "timestamp": "2026-01-20T10:30:00Z",
  "doc_type": "runbook",
  "access_scope": "engineering",
  "page_number": 12
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Hybrid Retrieval

Vector search captures semantic meaning; keyword search ensures exact-match for identifiers (error codes like `ERR_502`, service names, version strings, API names); metadata filters narrow the candidate set by service, environment, version, region, document type.

```
Query ──▶ Embed ──▶ Vector Top-K
                         ├──┐
Query ──▶ Tokenize ──▶ Keyword Top-K
                         ├──┴──▶ Merge ──▶ Re-rank ──▶ Top 3–5 chunks
Filters (svc, env, ver) ─┘
```

Top-K stays small (3–5) — quality over quantity, with re-ranking driving the final order.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Hallucination Mitigation

- Strict system prompts that answer only from retrieved context, otherwise return "not enough context".
- Similarity thresholds and metadata filters on retrieval.
- Source citations on every answer (chunk ID, document, section, page).
- Re-rank Top-K before generation.
- **Validation Agent** checks answer faithfulness against retrieved chunks.
- Full RAG trace logged: query, chunk IDs, similarity scores, prompt version, response, latency, token usage.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Reliability and Production Controls

| Failure mode | Control |
|---|---|
| Parse errors, unsupported doc types | Per-doc-type parser, DLQ for unrecognized types |
| Embedding API failures | Retries with exponential backoff |
| Vector DB write failures | Idempotent ingestion + retry |
| Bedrock timeouts / rate limits | Timeouts, retries, queue-side throttling |
| Low-confidence retrieval | Refuse with "not enough context" instead of guessing |
| Tool-call failures | Wrapped retries, fallback responses, alerts |
| Repeat ingestion | Idempotent keys on S3 object → chunk ID |

Multi-layer caching reduces tail latency:
- Query embedding cache
- Top-K retrieval cache
- Final-answer cache (for stable knowledge only)
- Metadata cache

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Observability

Logged per request: user query, retrieved chunk IDs, similarity scores, prompt version, model response, latency (request, retrieval, Bedrock), token usage, tool-call success rate, errors, trace IDs, conversation IDs. Surfaced via CloudWatch metrics dashboards (Grafana / Prometheus / ELK alternatives are documented for non-AWS deployments).

Retrieval evaluation is tracked separately from generation evaluation:
- **Retrieval**: precision, Top-K hit rate, empty-result rate.
- **Generation**: answer faithfulness, latency, token usage, user feedback.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Security and Multi-Tenancy

- **Document-level access control** via per-chunk `access_scope` metadata enforced at retrieval time.
- **IAM** roles for service-to-service permissions.
- **KMS** encryption at rest for S3, DynamoDB, and vector store.
- **Secrets Manager** for API keys and connection strings.
- All tool calls written to an audit log for review.
- Sensitive context filtered before LLM injection.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Tech Stack

### AI / ML
- **LLM**: AWS Bedrock with LLaMA 3 (production); pluggable provider layer
- **Embeddings**: AWS Titan Embeddings (768-dim) or Sentence Transformers (`all-MiniLM-L6-v2`)
- **Frameworks**: LangChain + LangGraph (ReAct, structured prompts, tool calling)
- **Retrieval**: hybrid semantic + keyword + metadata + re-ranking

### Cloud and Infrastructure (AWS-native)
- **Compute**: AWS Lambda (serverless query and ingestion workers)
- **API**: API Gateway (REST exposure) + FastAPI handlers
- **Storage**: S3 (raw uploads), DynamoDB / PostgreSQL (metadata + conversation state)
- **Async**: SQS (ingestion event queue), Step Functions (multi-step ingestion orchestration)
- **Vector DB**: OpenSearch Serverless / pgvector (Aurora) — production; FAISS / ChromaDB / Pinecone documented as alternatives
- **Observability**: CloudWatch logs and metrics, structured JSON logs, trace IDs, request IDs
- **IaC**: Terraform
- **Security**: IAM, KMS, Secrets Manager

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI (API Gateway-fronted Lambda handlers)
- **Reliability**: timeouts, retries with exponential backoff, dead-letter queues, idempotent ingestion, multi-layer caching

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

- AWS account with access to Bedrock (LLaMA 3) and Titan Embeddings
- Python 3.10+
- Terraform 1.5+
- An OpenSearch Serverless collection or a Postgres instance with pgvector

### Installation

```bash
git clone https://github.com/virtual457/agentic-rag-document-platform.git
cd agentic-rag-document-platform
cd backend

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configure `.env`

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=meta.llama3-70b-instruct-v1:0
EMBEDDINGS_PROVIDER=titan
EMBEDDINGS_MODEL=amazon.titan-embed-text-v1
VECTOR_BACKEND=opensearch                  # or pgvector
OPENSEARCH_ENDPOINT=https://...aoss.amazonaws.com
DYNAMODB_TABLE_METADATA=rag-doc-metadata
S3_BUCKET_INGEST=rag-doc-ingest
SQS_INGEST_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../ingest
JIRA_BASE_URL=https://your-org.atlassian.net
SERVICENOW_BASE_URL=https://your-org.service-now.com
```

### Provision infrastructure

```bash
cd infra/terraform
terraform init
terraform apply
```

### Run the API locally (against deployed AWS resources)

```bash
cd backend
uvicorn main:app --reload
# API:    http://localhost:8000
# Docs:   http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### Ingest documents

Upload to the ingestion S3 bucket; SQS triggers the Step Functions ingestion worker which parses, chunks, embeds, and indexes. Status is observable via CloudWatch.

```bash
aws s3 cp ./samples/payment-runbook.pdf s3://rag-doc-ingest/runbooks/
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

```
agentic-rag-document-platform/
│
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   │
│   ├── src/
│   │   ├── agents/                      # LangGraph agent graph
│   │   │   ├── router.py               # Query Router
│   │   │   ├── retrieval.py            # Retrieval Agent
│   │   │   ├── reasoning.py            # Reasoning Agent (ReAct)
│   │   │   ├── validation.py           # Validation Agent
│   │   │   └── action.py               # Action Agent + tool calls
│   │   │
│   │   ├── ingestion/                   # Ingestion workers
│   │   │   ├── parser.py
│   │   │   ├── chunker.py              # section-aware + event-based
│   │   │   ├── embedder.py             # Titan / Sentence Transformers
│   │   │   └── indexer.py              # OpenSearch / pgvector writes
│   │   │
│   │   ├── retrieval/
│   │   │   ├── hybrid.py               # vector + keyword + metadata
│   │   │   ├── reranker.py
│   │   │   └── cache.py
│   │   │
│   │   ├── llm/
│   │   │   ├── bedrock.py              # LLaMA 3 client
│   │   │   └── prompts/                # system prompts + guardrails
│   │   │
│   │   ├── tools/
│   │   │   ├── jira.py
│   │   │   ├── servicenow.py
│   │   │   ├── email.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── observability/
│   │   │   ├── logger.py               # structured JSON logs, trace IDs
│   │   │   └── metrics.py              # CloudWatch metric emitters
│   │   │
│   │   └── security/
│   │       ├── access_scope.py         # per-chunk access enforcement
│   │       └── secrets.py              # Secrets Manager wrappers
│   │
│   ├── api/                             # FastAPI routes
│   ├── config/
│   └── tests/
│
├── infra/
│   └── terraform/                       # Lambda, API Gateway, S3, SQS,
│                                        # Step Functions, OpenSearch,
│                                        # IAM, KMS, Secrets Manager
│
├── docs/                                # Architecture and operations
│
└── README.md
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

### Completed
- [x] LangGraph multi-agent orchestrator (Router → Retrieval → Reasoning → Validation → Action)
- [x] AWS Bedrock LLaMA 3 generation with strict grounding prompts
- [x] AWS Titan Embeddings + OpenSearch hybrid retrieval with re-ranking
- [x] Section-aware chunking for docs, event-based chunking for logs
- [x] Tool-calling: Jira, ServiceNow, email, audit logging
- [x] Validation Agent with faithfulness checks and refusal-on-low-confidence
- [x] Production controls: timeouts, retries, DLQs, idempotent ingestion
- [x] Multi-layer caching (embedding / retrieval / answer / metadata)
- [x] CloudWatch observability with trace IDs and per-stage latency
- [x] Multi-tenant per-chunk access scope + IAM/KMS/Secrets Manager

### In Progress
- [ ] pgvector backend parity with OpenSearch
- [ ] Streaming responses end-to-end (Bedrock → API → client)
- [ ] Eval harness with retrieval/generation metric dashboards

### Planned
- [ ] Cross-document reasoning (multi-hop retrieval)
- [ ] Agentic auto-RCA from telemetry log clusters
- [ ] Per-tenant prompt customization
- [ ] On-call assistant integrations (PagerDuty, Slack)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

**Chandan Gowda K S**

- chandan.keelara@gmail.com
- [LinkedIn](https://www.linkedin.com/in/chandan-gowda-k-s-765194186/)
- [GitHub @virtual457](https://github.com/virtual457)
- [Portfolio](https://virtual457.github.io)

**Project Link**: [github.com/virtual457/agentic-rag-document-platform](https://github.com/virtual457/agentic-rag-document-platform)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS -->
[contributors-shield]: https://img.shields.io/github/contributors/virtual457/agentic-rag-document-platform.svg?style=for-the-badge
[forks-shield]: https://img.shields.io/github/forks/virtual457/agentic-rag-document-platform.svg?style=for-the-badge
[stars-shield]: https://img.shields.io/github/stars/virtual457/agentic-rag-document-platform.svg?style=for-the-badge
[issues-shield]: https://img.shields.io/github/issues/virtual457/agentic-rag-document-platform.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/virtual457/agentic-rag-document-platform.svg?style=for-the-badge
[contributors-url]: https://github.com/virtual457/agentic-rag-document-platform/graphs/contributors
[forks-url]: https://github.com/virtual457/agentic-rag-document-platform/network/members
[stars-url]: https://github.com/virtual457/agentic-rag-document-platform/stargazers
[issues-url]: https://github.com/virtual457/agentic-rag-document-platform/issues
[license-url]: https://github.com/virtual457/agentic-rag-document-platform/blob/master/LICENSE
