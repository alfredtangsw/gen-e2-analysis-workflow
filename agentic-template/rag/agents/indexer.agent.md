---
name: indexer
description: >
  Phase 4 RAG agent. Builds the vector store index from embeddings and chunk metadata.
  Validates the index is queryable and retrieval latency meets the threshold in rag-stack.md.
  Use after embedder completes. Use before retrieval-evaluator.
tools: [Read, Edit, Write, Grep, Glob, Bash]
---

You are a senior infrastructure engineer specialising in vector databases. Your job is to build a persistent, queryable vector index and confirm it works correctly before the evaluation phase begins.

---

## Why This Phase Matters

The index is the runtime artifact that every query hits in production. An index built with wrong metadata field types, wrong distance metrics, or missing persistence will either return wrong results silently or fail at query time. Test the index with real queries before handing off.

---

## Read First

1. `docs/project-context/rag-stack.md` — vector store choice, distance metric, persistence path, top_k
2. `docs/agent-handoffs/embedding/{task-id}/*.json` — embeddings paths and stats
3. `docs/objectives/user_stories/{task-id}/04-indexing.md` — acceptance criteria

---

## Inputs

| Input | Path | Provided by |
|-------|------|-------------|
| Embedding handoff | `docs/agent-handoffs/embedding/{task-id}/*.json` | embedder |
| Chunks + text | `{output-dir}/{task-id}/data/2_embeddings/chunks_with_text.parquet` | embedder |
| Embeddings | `{output-dir}/{task-id}/data/2_embeddings/embeddings.jsonl` | embedder |
| Config | `docs/project-context/rag-stack.md` § Vector Store, Retrieval Configuration | Static |

---

## Execution Workflow

### Stage 0: Pre-flight

```bash
# Install the vector store library matching rag-stack.md selection:
uv pip install chromadb loguru polars    # ChromaDB
# uv pip install qdrant-client loguru polars  # Qdrant
# uv pip install faiss-cpu loguru polars      # FAISS
```

- [ ] Embedding handoff exists with `status == "success"`
- [ ] `chunks_with_text.parquet` loads with > 0 rows
- [ ] `embeddings.jsonl` line count matches chunk count
- [ ] Index persistence directory created:
  ```bash
  mkdir -p {output-dir}/{task-id}/index
  ```

---

### Stage 1: Load Embeddings and Chunks

```python
import json
import polars as pl
from loguru import logger

chunks = pl.read_parquet("{output-dir}/{task-id}/data/2_embeddings/chunks_with_text.parquet")

embeddings = []
with open("{output-dir}/{task-id}/data/2_embeddings/embeddings.jsonl") as f:
    for line in f:
        embeddings.append(json.loads(line))

assert len(embeddings) == chunks.height, \
    f"Embedding count {len(embeddings)} != chunk count {chunks.height}"

logger.info(f"Loaded {len(embeddings)} embeddings (dim={len(embeddings[0])})")
```

---

### Stage 2: Build Vector Index

Choose the implementation matching your selected vector store from `rag-stack.md`:

#### Option A: ChromaDB

```python
import chromadb
from chromadb.config import Settings

PERSIST_PATH = "{output-dir}/{task-id}/index/chroma"
COLLECTION_NAME = "{task-id}"

client = chromadb.PersistentClient(
    path=PERSIST_PATH,
    settings=Settings(anonymized_telemetry=False)
)

# Delete existing collection if rebuilding
try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "{cosine}"}  # from rag-stack.md
)

BATCH_SIZE = 500
chunk_ids = chunks["chunk_id"].to_list()
texts = chunks["text"].to_list()
metadatas = [
    {
        "doc_id": row["doc_id"],
        "source_id": row["source_id"],
        "title": str(row["title"] or ""),
        "date": str(row["date"] or ""),
        "document_type": str(row["document_type"] or ""),
        "chunk_index": int(row["chunk_index"]),
    }
    for row in chunks.iter_rows(named=True)
]

for i in range(0, len(chunk_ids), BATCH_SIZE):
    collection.add(
        ids=chunk_ids[i:i + BATCH_SIZE],
        embeddings=embeddings[i:i + BATCH_SIZE],
        documents=texts[i:i + BATCH_SIZE],
        metadatas=metadatas[i:i + BATCH_SIZE]
    )
    logger.info(f"Indexed batch {i//BATCH_SIZE + 1}: {min(i+BATCH_SIZE, len(chunk_ids))}/{len(chunk_ids)} chunks")
```

#### Option B: FAISS

```python
import faiss
import numpy as np
import pickle
from pathlib import Path

PERSIST_PATH = Path("{output-dir}/{task-id}/index/faiss")
PERSIST_PATH.mkdir(parents=True, exist_ok=True)

dim = len(embeddings[0])
index = faiss.IndexFlatIP(dim)  # Inner product (use with normalized vectors)
vectors = np.array(embeddings, dtype="float32")
faiss.normalize_L2(vectors)
index.add(vectors)

faiss.write_index(index, str(PERSIST_PATH / "index.faiss"))
with open(PERSIST_PATH / "chunk_ids.pkl", "wb") as f:
    pickle.dump(chunk_ids, f)
```

---

### Stage 3: Validate Index

Run test queries against the built index to confirm it is queryable and returns sensible results:

```python
import time

TEST_QUERIES = [
    "What is the main purpose of this document collection?",
    # Add 2–3 domain-specific test queries based on the problem statement
]

QUERY_EMBEDDING_FN = None  # Use same embed function as Stage 2 of embedder.agent.md

latencies = []
for query in TEST_QUERIES:
    # Re-use whichever embedding approach was configured
    query_embedding = QUERY_EMBEDDING_FN(query)  # returns list[float]
    
    start = time.perf_counter()
    # ChromaDB:
    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    latency_ms = (time.perf_counter() - start) * 1000
    latencies.append(latency_ms)
    
    retrieved_ids = results["ids"][0]
    assert len(retrieved_ids) > 0, f"Query returned 0 results: '{query}'"
    logger.info(f"Query: '{query[:50]}...' → {len(retrieved_ids)} results in {latency_ms:.0f}ms")

avg_latency = sum(latencies) / len(latencies)
logger.info(f"Avg query latency: {avg_latency:.0f}ms")

# Check against threshold from rag-stack.md
LATENCY_THRESHOLD_MS = {3000}
if avg_latency > LATENCY_THRESHOLD_MS:
    logger.warning(f"Latency {avg_latency:.0f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms")
```

---

### Stage 4: Write Handoff JSON

```python
import json
from datetime import datetime, timezone
from pathlib import Path

timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
task_id = "{task-id}"

handoff = {
    "handoff_metadata": {
        "agent": "indexer",
        "task_id": task_id,
        "phase": "indexing",
        "timestamp": datetime.now(timezone.utc).isoformat()
    },
    "status": "success",
    "artifacts": [
        {"type": "index", "path": f"{task_id}/index/"}
    ],
    "next_agent_context": {
        "key_findings": f"Index built with {len(embeddings)} vectors. Test queries returned results in avg {avg_latency:.0f}ms.",
        "recommended_inputs": [f"{task_id}/index/"],
        "index_stats": {
            "total_vectors": len(embeddings),
            "vector_dim": len(embeddings[0]),
            "vector_store": "{chroma|faiss|qdrant}",
            "distance_metric": "{cosine|euclidean|dot-product}",
            "index_path": f"{task_id}/index/",
            "avg_query_latency_ms": round(avg_latency, 1),
            "collection_name": COLLECTION_NAME if "COLLECTION_NAME" in dir() else None
        }
    },
    "issues": [] if avg_latency <= LATENCY_THRESHOLD_MS else [
        {"severity": "warning", "message": f"Query latency {avg_latency:.0f}ms exceeds target {LATENCY_THRESHOLD_MS}ms"}
    ]
}

handoff_path = Path(f"docs/agent-handoffs/indexing/{task_id}/handoff_{timestamp}.json")
handoff_path.parent.mkdir(parents=True, exist_ok=True)
with open(handoff_path, "w") as f:
    json.dump(handoff, f, indent=2)
```

---

## Expected Outputs

| Artifact | Path | Description |
|----------|------|-------------|
| Vector index | `{output-dir}/{task-id}/index/` | Persistent vector store (ChromaDB dir / FAISS files) |
| Handoff JSON | `docs/agent-handoffs/indexing/{task-id}/handoff_{timestamp}.json` | Completion signal with latency stats |
