# AI Workflow System — Learnings

# AI Build Master Roadmap

## Project Philosophy

Learn While Building

### Principles

1. Build a simple working implementation first.
2. Complete an end-to-end capability before introducing complexity.
3. Progress toward production-capable architecture.
4. Experiment with alternative technologies after the capability works.
5. Document tradeoffs, costs, ROI, and operational implications.
6. Compare implementations to understand engineering decisions.

### Learning Approach

Capability First
      ↓
Simple Working Implementation
      ↓
End-to-End Completion
      ↓
Production-Capable Implementation
      ↓
Technology Experiments
      ↓
Tradeoff Analysis
      ↓
Cost / ROI Analysis

### Examples From This Project

Frontend Evolution

Streamlit
    ↓
HTML/CSS/JavaScript

Retrieval Evolution

BM25
   ↓
Embeddings

Future Vector Database Evolution

FAISS
   ↓
Qdrant / Pinecone / Chroma

Deployment Evolution

Local Development
    ↓
Render
    ↓
AWS

## Master Roadmap

### Phase 1 — Workflow Foundations ✅

1.1 Basic AI Prompting
1.2 FastAPI Backend Architecture
1.3 Confidence & Validation

### Phase 2 — AI Product Foundations ✅

2.1 Streamlit Application
2.2 OCR Document Ingestion
2.3 Structured Rendering (Streamlit)
2.4 Frontend Transition (HTML/CSS/JS)
2.5 Advanced Structured Rendering
2.6 Engineering Discipline & Debugging

### Phase 3 — Retrieval Foundations ✅

3.1 Basic RAG Foundations
3.2 Prompt Reasoning Improvements
3.3 BM25 Retrieval Engineering

### Phase 4 — Semantic Retrieval ✅

4.1 Embeddings
4.2 Cosine Similarity
4.3 Semantic Retrieval

### Phase 5 — Vector Databases (Current Phase)

Goal:
Move from in-memory vector search to scalable vector indexing.

Learning Path:
5.1 FAISS

Production Recommendation:
Qdrant

Technology Experiments:
5.2 Chroma
5.3 Qdrant
5.4 Pinecone
5.5 Weaviate

### Phase 6 — Hybrid Retrieval

Learning Path:
BM25 + Embeddings + RRF

Production Recommendation:
Hybrid Retrieval Pipeline

Technology Experiments:
LangChain Retrievers
Custom Hybrid Search

### Phase 6.5 — Knowledge Graph Retrieval

Goal:
Add a third retrieval mode — graph traversal — for the one class of question BM25/embeddings/hybrid can't answer: multi-hop relational queries (drug↔drug interactions, drug↔condition contraindications, patient↔prescription↔drug history).

Prerequisite (blocking):
Phase 6 (Hybrid Retrieval) complete. A KG retriever is evaluated against, and routed alongside, BM25 + embeddings — building it before hybrid retrieval exists means there's nothing to compare it to.

Seed Dataset (must exist before any graph is built — none of this data exists in the repo today):
- ~20-30 hand-curated drug-drug interaction pairs, scoped to what's already in `knowledge_base/` (anticoagulants, NSAIDs, opioids, antibiotics — reuse `antibiotics_guidelines.md` as the starting entity list)
- ~10 drug-condition contraindication pairs (e.g., NSAID ↔ renal impairment)
- 5-10 synthetic multi-prescription patient histories (same synthetic-data pattern as the ER Triage project's `ER_AI_Assist_Synthetic_1000_Patients`, scaled down to a handful of patients with 2-3 prescriptions each so there are real multi-hop paths to traverse)
- Store as source CSV/JSON in `knowledge_base/graph_seed/` before any graph-building code is written

Learning Path (simple first):
6.5.1 NetworkX — in-memory Python graph, zero infrastructure, enough to prove the traversal logic and query patterns work before adding a database

Production Recommendation:
Neo4j — property graph + Cypher query language; standard for this domain, pairs with LangChain/LlamaIndex GraphRAG retrievers

Technology Experiments:
6.5.2 Neo4j
6.5.3 Amazon Neptune
6.5.4 ArangoDB (multi-model, compare against a dedicated graph DB)

Eval Criteria (the actual justification step — do this before calling the phase done):
- Build a small eval set of multi-hop questions the seed data supports (e.g., "Patient is on Drug A — is Drug B safe to add given their condition?")
- Run the same eval set through: (1) hybrid retrieval alone, (2) graph traversal alone, (3) hybrid + graph combined
- Record precision/recall per method in a results doc, same pattern as `tests/test_retrieval_evaluation.py`
- Only keep the graph in the production path if it measurably beats hybrid-alone on the multi-hop question set — this phase is explicitly allowed to conclude "not worth it yet" if the seed dataset is too small to show a real gap

### Phase 7 — Evaluation & Observability

Technology Experiments:
LangSmith
Weights & Biases Weave
OpenTelemetry
Custom Evaluation Framework
(include the Phase 6.5 graph-vs-hybrid eval results in this phase's scope, not as a one-off)

### Phase 8 — Agent Foundations

Technology Experiments:
Pure Python Agents
LangChain Agents
PydanticAI
OpenAI Tool Calling

### Phase 9 — LangGraph Workflows

Technology Experiments:
LangGraph
CrewAI
AutoGen
Semantic Kernel

### Phase 10 — Memory Systems

Technology Experiments:
Airtable
PostgreSQL
Redis
SQLite
Vector Memory

### Phase 11 — Multi-Agent Systems

Technology Experiments:
LangGraph
CrewAI
AutoGen
Agent-to-Agent Communication

### Phase 12 — AI Product Engineering

Learning Path:
Render

Production Recommendation:
AWS

Technology Experiments:
Google Cloud
Railway
Fly.io
Docker
GitHub Actions
n8n

## Current Status

Completed:
- Workflow Foundations
- AI Product Foundations
- Retrieval Foundations
- Semantic Retrieval

Current Focus:
- Phase 5.1 FAISS

---

# Phase 1 — Basic AI Prompting

## What Was Built
- Simple OpenAI prompt execution
- Prescription and referral extraction
- JSON response generation

## Key Learning
LLMs can generate structured outputs from unstructured healthcare text.

## Concepts Learned
- Prompt engineering
- Structured JSON extraction
- OpenAI API integration
- Backend API execution

---

# Phase 2 — FastAPI Backend Architecture

## What Was Built
- FastAPI backend service
- API endpoints
- Request/response schema handling
- Document type routing

## Key Learning
AI systems require orchestration layers, not just prompts.

## Concepts Learned
- Backend APIs
- Request schemas
- Response standardization
- Workflow routing
- Separation of concerns

---

# Phase 3 — Confidence & Validation Systems

## What Was Built
- High / Medium / Low confidence scoring
- Issue detection
- Recommendation generation
- Error handling responses

## Key Learning
AI systems must communicate uncertainty.

## Concepts Learned
- Confidence scoring
- Validation logic
- Human review workflows
- Ambiguity handling
- Trust communication in AI systems

---

# Phase 4 — Frontend Transition

## What Was Built
- Migration from Streamlit to HTML/CSS/JS
- FastAPI frontend integration
- API-based rendering

## Key Learning
Real AI products require frontend/backend separation.

## Concepts Learned
- HTML frontend structure
- JavaScript API calls
- CSS styling
- Static file serving
- Frontend/backend architecture

---

# Phase 5 — Structured Rendering

## What Was Built
- Confidence banner rendering
- Summary rendering
- Issues rendering
- Recommendation rendering
- Medication cards

## Key Learning
AI responses should be interpreted into UI components, not shown as raw JSON.

## Concepts Learned
- Structured rendering
- Dynamic UI rendering
- Conditional rendering
- Component-based frontend design
- AI UX patterns

---

# Phase 6 — Debugging & Engineering Discipline

## Challenges Faced
- HTML accidentally written into Python files
- JavaScript written into HTML templates
- Static file caching issues
- Browser cache problems
- File structure confusion

## Key Learning
File separation and architecture discipline are critical in software engineering.

## Concepts Learned
- Browser caching
- Cache busting
- Static asset management
- File structure discipline
- Debugging workflow
- Frontend troubleshooting

---

# Phase 7 — Basic RAG Foundations

## What Was Built
- knowledge_base folder
- Guideline text files
- Retrieval loader
- Context injection into prompts

## Key Learning
LLMs can be grounded using external knowledge instead of relying only on model memory.

## Concepts Learned
- Retrieval-Augmented Generation (RAG)
- Knowledge grounding
- Runtime context injection
- External knowledge systems
- Knowledge-aware prompting

---

# Phase 8 — Prompt Reasoning Improvements

## What Was Improved
- PRN vs duration handling
- Medication reasoning improvements
- Domain-aware extraction rules

## Key Learning
AI systems require domain-specific reasoning constraints in addition to retrieval.

## Concepts Learned
- Prompt constraints
- Domain semantics
- Clinical workflow interpretation
- Reasoning guidance
- Rule-assisted prompting

---

# Phase 9 — Retrieval Engineering Foundations

## What Was Built
- knowledge_base folder structure
- Domain-specific knowledge documents
- Document loader (`loader.py`)
- Chunking engine (`chunker.py`)
- Chunk metadata model
- BM25 retrieval engine (`retriever.py`)
- Retrieval testing workflow

## Knowledge Base Created

The knowledge base was separated from user-uploaded documents.

Knowledge documents include:
- antibiotic guidelines
- prescription validation rules
- referral validation rules
- confidence evaluation rules

Key learning:

User uploads are inputs.

Knowledge base documents are the searchable corpus used for retrieval.

## Key Learning

Retrieval is a separate system from the LLM.

Before this phase:

Prescription
    ↓
Prompt
    ↓
LLM

After this phase:

Knowledge Base
      ↓
Loader
      ↓
Chunker
      ↓
Retriever
      ↓
Relevant Knowledge

The system now retrieves relevant information instead of relying on the entire knowledge base being injected into the prompt.

## Concepts Learned

### Knowledge Corpus Design
- Difference between input documents and knowledge documents
- Building a searchable knowledge base
- Organizing domain knowledge

### Document Loading
- Converting files into structured document objects
- Standardized document representation
- Category and source tracking

### Chunking
- Breaking large documents into smaller retrieval units
- Chunk size and overlap concepts
- Retrieval granularity
- Context preservation

### Metadata
- Source tracking
- Category tagging
- Traceability
- Retrieval debugging

### BM25 Retrieval
- Keyword-based retrieval
- Tokenization
- Relevance scoring
- Ranking search results
- Top-K retrieval

### Retrieval Evaluation
- Testing retrieval quality
- Verifying relevance of returned chunks
- Understanding retrieval failures
- Measuring retrieval accuracy

## Most Important Insight

RAG is not:

LLM + Documents

RAG is:

Retrieval
+
Generation

Today focused entirely on the Retrieval portion.

The LLM has not yet been connected to the retriever.

## Current Learning Stage

### Current Status

Completed:
- Knowledge base creation
- Document loading
- Chunk generation
- Metadata creation
- BM25 retrieval
- Retrieval testing

### Your NEXT STEP

Connect retrieval results to the OpenAI workflow.

Build:

Question
      ↓
Retriever
      ↓
Relevant Chunks
      ↓
Prompt Context
      ↓
LLM
      ↓
Answer

### This Teaches
- Retrieval-Augmented Generation (RAG)
- Context construction
- Prompt grounding with retrieved knowledge
- End-to-end RAG architecture

### Why This Matters

This becomes the bridge between:

retrieval systems

and:

semantic retrieval using embeddings and vector databases.

---

---

# Phase 10 — Embeddings & Semantic Retrieval

## What Was Built

- OpenAI embedding integration (`embedding.py`)
- Embedding generation using `text-embedding-3-small`
- Cosine similarity engine (`similarity.py`)
- Semantic similarity testing
- Semantic retriever (`semantic_retriever.py`)
- Embedding-based retrieval evaluation

## Key Learning

Embeddings transform text into vectors that represent meaning rather than words.

This enables semantic retrieval, where different words expressing similar concepts can still be matched.

---

## BM25 Failure Demonstrated

Query:

```text
drug course length
```

Expected concept:

```text
antibiotic duration
```

BM25 Result:

```text
Score = 0.00
```

for all chunks.

Reason:

BM25 requires keyword overlap.

---

## First Embedding Generated

Created:

```text
rag/embedding.py
```

Model:

```text
text-embedding-3-small
```

Observation:

The embedding returned a vector containing:

```text
1536 dimensions
```

### What A Vector Is

A vector is a numerical representation of meaning.

Example:

```text
Text
   ↓
Embedding Model
   ↓
[0.12, -0.45, 0.88, ...]
```

The vector represents the location of a piece of text within a high-dimensional semantic space.

---

## Cosine Similarity

Cosine similarity measures how similar two vectors are.

Purpose:

```text
Vector A
      ↓
Cosine Similarity
      ↑
Vector B
```

Higher scores indicate more similar meanings.

---

## Semantic Similarity Experiment

Results:

| Text A | Text B | Similarity |
|----------|----------|----------|
| antibiotic duration | drug course length | 0.5351 |
| antibiotic duration | referral specialist | 0.1008 |
| missing specialty information | specialist details absent | 0.6531 |

Key observation:

Different words can still produce high similarity when they express the same idea.

---

## Semantic Retrieval Test

Query:

```text
drug course length
```

Top Result:

```text
antibiotics_guidelines.md
```

Similarity:

```text
0.4236
```

This was a successful retrieval.

The semantic retriever correctly identified the antibiotic duration guideline even though none of the query words appeared in the document.

---

## Most Important Insight

BM25 Retrieval:

```text
Query
   ↓
Keyword Match
   ↓
Results
```

Semantic Retrieval:

```text
Query
   ↓
Embedding
   ↓
Cosine Similarity
   ↓
Results
```

This is the architectural shift from keyword search to semantic search.

## Current Status

Completed:

- Embedding generation
- Vector representation
- Cosine similarity
- Semantic similarity testing
- Semantic retrieval

## Next Step

Build a vector index using FAISS.

Goal:

```text
Embeddings
      ↓
Vector Index
      ↓
Fast Similarity Search
      ↓
Scalable Semantic Retrieval
```

# Future Learning Roadmap

## Upcoming Topics
- Embeddings
- FAISS
- Vector databases
- Semantic search
- Hybrid retrieval
- LangChain retrievers
- LangSmith observability
- LangGraph workflows
- Enterprise memory systems
- Agentic workflows

## Long-Term Goal

Move from:

prompt-driven AI applications

To:

intelligent AI workflow systems with retrieval, memory, reasoning, observability, and orchestration.
