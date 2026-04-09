# RAG Stack

<!--
TEMPLATE: Fill in this file before running any prompts.
This replaces tech-stack.md for RAG projects.
Covers: vector DB, embedding model, LLM, chunking strategy, framework.
-->

## Selected Stack

| Component | Selected Option | Justification |
|-----------|----------------|---------------|
| **Framework** | {LangChain \| LlamaIndex \| Haystack \| custom} | {why} |
| **Embedding model** | {see options below} | {why} |
| **Vector store** | {see options below} | {why} |
| **LLM** | {see options below} | {why} |
| **Evaluation framework** | {RAGAS \| TruLens \| custom} | {why} |

---

## Component Options & Constraints

### Embedding Model

Choose one. Document the selected option and why alternatives were rejected.

| Option | Dimensions | Cost | Latency | Notes |
|--------|------------|------|---------|-------|
| `text-embedding-3-small` (OpenAI) | 1536 | Low ($) | ~50ms | Requires API key |
| `text-embedding-3-large` (OpenAI) | 3072 | Medium ($$) | ~80ms | Higher quality |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Free (local) | ~10ms | Good for short texts |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Free (local) | ~20ms | Better quality, larger |
| `nomic-embed-text` (via Ollama) | 768 | Free (local) | ~30ms | No external API needed |
| `{custom}` | | | | |

**Selected**: `{model-name}`
**Embedding dimension**: {N}
**Batch size for generation**: {N} (balance between speed and memory)

---

### Vector Store

| Option | Deployment | Persistent | Filtering | Scale | Notes |
|--------|-----------|------------|-----------|-------|-------|
| ChromaDB | Local / Docker | Yes | Yes | Medium | Good for prototyping |
| FAISS | In-memory / Local | With serialization | No | Large | Fast, no server needed |
| Qdrant | Local / Cloud | Yes | Yes | Large | Production-ready |
| Pinecone | Cloud only | Yes | Yes | Very large | Managed, paid |
| Weaviate | Local / Cloud | Yes | Yes | Large | GraphQL interface |

**Selected**: `{vector-store}`
**Persistence path**: `{output-dir}/{task-id}/index/`
**Index name**: `{task-id}`
**Distance metric**: {cosine \| euclidean \| dot-product}

---

### LLM

| Option | Hosting | Cost | Context window | Notes |
|--------|---------|------|---------------|-------|
| GPT-4o (OpenAI) | Cloud | $$$ | 128k | Highest quality |
| GPT-4o-mini (OpenAI) | Cloud | $ | 128k | Good cost/quality ratio |
| Claude 3.5 Sonnet (Anthropic) | Cloud | $$ | 200k | Strong reasoning |
| Llama 3.1 (via Ollama) | Local | Free | 128k | No API key needed |
| Mistral 7B (via Ollama) | Local | Free | 32k | Lightweight |
| `{custom}` | | | | |

**Selected**: `{model-name}`
**API base**: `{https://api.openai.com/v1 or http://localhost:11434}`
**Env var for key**: `{LLM_API_KEY or OPENAI_API_KEY}`
**Max tokens for generation**: {N}
**Temperature**: {0.0 for factual RAG is recommended}

---

## Chunking Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Strategy** | {fixed-size \| recursive-character \| semantic \| sentence} | {why} |
| **Chunk size** (tokens) | {256–1024} | {based on avg document section length and context window} |
| **Chunk overlap** (tokens) | {20–100} | {prevents context loss at boundaries} |
| **Separator hierarchy** | {`\n\n`, `\n`, `. `, ` `} | {for recursive strategy} |

**Special handling by document type**:

| Document type | Override strategy | Notes |
|---------------|------------------|-------|
| {PDF tables} | {preserve table as single chunk} | {tables lose meaning when split} |
| {Code blocks} | {preserve as single chunk} | {code context is non-separable} |
| {Short documents < 200 tokens} | {keep as single chunk} | {no benefit from splitting} |

---

## Retrieval Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| **top_k** (chunks retrieved per query) | {5–10} | {tune based on recall eval results} |
| **Retrieval strategy** | {similarity \| MMR \| hybrid} | {MMR reduces duplicate results} |
| **MMR lambda** (if using MMR) | {0.5} | {0 = max diversity, 1 = max similarity} |
| **Score threshold** (minimum similarity) | {0.7} | {reject low-confidence results} |
| **Reranker** | {None \| Cohere Rerank \| cross-encoder} | {reranker improves precision at cost of latency} |

---

## Quality Thresholds

Minimum acceptable scores before the pipeline is considered complete. Adjust based on use case.

| Metric | Minimum threshold | Blocking? |
|--------|------------------|-----------|
| Retrieval precision@5 | {0.75} | Yes — re-tune chunking/retrieval if below |
| Retrieval recall@5 | {0.70} | Yes |
| MRR | {0.65} | Yes |
| RAGAS faithfulness | {0.80} | Yes — answers must be grounded in retrieved context |
| RAGAS answer relevance | {0.75} | Yes |
| RAGAS context precision | {0.70} | Warning only |
| End-to-end latency (p95) | {< 3s} | Warning only |

---

## Runtime Environment

| Requirement | Value |
|-------------|-------|
| Python version | {3.10+} |
| Package manager | {uv} |
| GPU required? | {No \| Optional (for local embedding) \| Required} |
| Min RAM | {8GB \| 16GB for local LLM} |
| Key packages | `langchain`, `chromadb`, `sentence-transformers`, `ragas`, `loguru` |

---

## Environment Variables Required

```bash
# Copy to .env (never commit real values)
LLM_API_KEY=             # OpenAI / Anthropic key (leave blank if using local)
EMBEDDING_API_KEY=       # If using OpenAI embeddings
VECTOR_STORE_URL=        # Remote vector store URL (if not local)
VECTOR_STORE_API_KEY=    # Remote vector store key (if applicable)
```
