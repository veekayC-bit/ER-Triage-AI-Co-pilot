# Building an AI Workflow Application: From Prompting to Structured AI Systems

## Initial Goal

The original objective was not just to “use AI,” but to understand how real AI-powered workflow systems are built end-to-end.

The application started as a very simple healthcare document parser:
- Input prescription or referral text
- Send prompt to OpenAI
- Return extracted JSON

At the beginning, the system behaved more like:
- a prompt playground
- a raw API wrapper
- an engineering experiment

The architecture was extremely minimal:

```text
Frontend Input
↓
OpenAI Prompt
↓
Raw JSON Output
```

This worked technically, but it was not a usable AI application.

---

# Phase 1 — Backend AI Extraction

The first evolution focused on building a proper backend service using:
- FastAPI
- OpenAI API
- Prompt engineering
- Structured JSON extraction

We introduced:
- document type routing
- prescription extraction
- referral extraction
- standardized JSON responses

Key concepts implemented:
- request schemas
- response normalization
- confidence handling
- validation logic
- issue detection

This shifted the project from:

```text
single prompt experiment
```

to:

```text
backend AI extraction service
```

---

# Phase 2 — Confidence & Validation Layer

One of the biggest realizations was:
AI extraction alone is not enough.

Real workflow systems need:
- trust indicators
- validation
- ambiguity handling
- fallback mechanisms

We implemented:
- High / Medium / Low confidence
- issue arrays
- recommendation generation
- standardized error responses

This introduced an important AI product principle:

```text
AI systems must communicate uncertainty.
```

This was a major shift from:

```text
“AI gave an answer”
```

to:

```text
“AI evaluated the reliability of its answer”
```

---

# Phase 3 — Transition Away From Streamlit

Initially, the frontend relied on Streamlit for quick prototyping.

However, limitations became obvious:
- difficult UI control
- weak frontend flexibility
- harder scaling into real product UX

Decision made:

```text
Move fully to HTML/CSS/JavaScript
```

This became a major architectural turning point.

The application evolved into:

```text
Frontend (HTML/CSS/JS)
↓
FastAPI API Layer
↓
LLM Processing
```

This introduced:
- API-driven frontend rendering
- frontend/backend separation
- client-side rendering logic
- static asset management

---

# Phase 4 — Structured Rendering

This was one of the hardest and most important phases.

Initially:
- AI responses were dumped as raw JSON
- users saw backend data directly
- no UX interpretation existed

We redesigned the frontend into structured rendering components:
- confidence banner
- summary section
- issues section
- recommendation section

The frontend evolved from:

```text
AI → JSON → User
```

to:

```text
AI → Interpretation Layer → UI Components → User
```

This is where the application started behaving like a real AI product instead of a debugging tool.

---

# Major Technical Challenges Faced

## 1. Frontend/Backend Separation Problems

During refactoring:
- HTML was accidentally written into `main.py`
- JavaScript was written into HTML templates
- Python code was overwritten by frontend code

This exposed an important engineering lesson:

```text
File separation and architecture discipline matter.
```

The final structure became:

```text
main.py              → backend
templates/index.html → HTML
static/script.js     → JS
static/style.css     → CSS
```

---

## 2. Static File & Browser Cache Issues

One of the most frustrating debugging phases involved:
- browser caching old JavaScript
- FastAPI static folder mismatches
- stale rendering logic

Problems encountered:
- `Static/` vs `static/`
- old JS still loading
- missing script requests
- stale confidence rendering

Fixes included:
- cache busting (`script.js?v=5`)
- correct static mounting
- proper file structure
- hard refresh debugging

This introduced an important frontend engineering concept:

```text
Browsers aggressively cache frontend assets.
```

---

## 3. Raw JSON Rendering Issues

Even after frontend rendering logic was implemented, raw JSON still appeared.

Root causes included:
- stale JS cache
- debug rendering left in place
- broken rendering blocks

Eventually:
- raw JSON rendering was removed
- component rendering became stable

This was the first point where:

```text
structured AI UX
```

actually worked end-to-end.

---

## 4. Dynamic Rendering Complexity

The application initially assumed all summary values were plain text.

However:

```json
"medications": [
  {...},
  {...}
]
```

introduced arrays of objects.

This forced the frontend to evolve into:
- dynamic rendering
- card-based layouts
- object iteration
- conditional rendering

This was a major frontend maturity step.

---

# Phase 5 — Product-Like UI

The frontend was upgraded from:

```text
unstyled developer prototype
```

to:

```text
structured AI workflow interface
```

Enhancements included:
- modern CSS layout
- card rendering
- confidence banners
- loading states
- styled buttons
- structured spacing
- medication cards

This transformed the experience from:

```text
engineering demo
```

to:

```text
AI application prototype
```

---

# Current Architecture

The system now operates as:

```text
Frontend (HTML/CSS/JS)
    ↓
FastAPI Backend
    ↓
Retrieval Layer (BM25 + Semantic Retrieval)
    ↓
Prompt Construction Layer
    ↓
LLM Extraction
    ↓
Confidence + Validation
    ↓
Structured Rendering
```

Current capabilities:
- prescription parsing
- referral parsing
- confidence scoring
- issue detection
- recommendation generation
- structured rendering
- API-based frontend architecture

---

# Phase 6 — Retrieval-Augmented Generation (RAG) Foundations

The next major evolution introduced the first true retrieval architecture into the application.

Before this phase, all available knowledge was loaded directly into prompts.

Architecture:

```text
Prescription / Referral
        ↓
All Knowledge
        ↓
Prompt
        ↓
LLM
```

This worked for small knowledge sets but could not scale.

The solution was to separate:

- user input documents
- knowledge documents

A dedicated knowledge base was created:

```text
knowledge_base/
├── prescriptions/
├── referrals/
└── validation/
```

Knowledge documents included:

- antibiotic guidelines
- prescription validation rules
- referral validation rules
- confidence evaluation rules

New retrieval components were implemented:

- Document Loader (`loader.py`)
- Chunking Engine (`chunker.py`)
- Metadata Model
- BM25 Retriever (`retriever.py`)

The architecture evolved into:

```text
Prescription / Referral
        ↓
Retriever
        ↓
Relevant Knowledge Chunks
        ↓
Prompt
        ↓
LLM
```

Key concepts implemented:

- Knowledge corpus design
- Document loading
- Chunking
- Metadata management
- Keyword retrieval
- Relevance ranking
- Retrieval evaluation

This was the first implementation of Retrieval-Augmented Generation (RAG).

Important distinction:

The system originally used:

BM25 keyword retrieval

A retrieval evaluation was performed to understand its limitations.

Example query:

```text
drug course length
```

Expected concept:

```text
antibiotic duration
```

BM25 result:

```text
Score = 0.00
```

for all chunks.

This demonstrated that BM25 requires keyword overlap and cannot reliably understand semantic meaning.

---

# Phase 7 — Embeddings & Semantic Retrieval

The next evolution focused on understanding how modern RAG systems perform semantic search.

The objective was to solve a limitation discovered during BM25 retrieval testing:

```text
Different words
Same meaning
Poor retrieval
```

Example:

```text
drug course length
```

should retrieve:

```text
antibiotic duration
```

but BM25 failed because the words did not match.

## Embedding Foundations

A new embedding layer was introduced:

```text
Text
    ↓
Embedding Model
    ↓
Vector
```

Implemented:

- OpenAI Embeddings (`text-embedding-3-small`)
- Embedding generation (`embedding.py`)
- Vector creation
- Semantic similarity evaluation

The first embedding generated a vector containing:

```text
1536 dimensions
```

This introduced the concept that text can be represented numerically in a semantic space.

## Cosine Similarity

A similarity engine was implemented:

```text
Vector A
      ↓
Cosine Similarity
      ↑
Vector B
```

This allowed semantic comparison between pieces of text.

Validation examples:

```text
antibiotic duration
↔
drug course length
```

Similarity:

```text
0.5351
```

and:

```text
missing specialty information
↔
specialist details absent
```

Similarity:

```text
0.6531
```

These experiments demonstrated that embeddings can identify related concepts even when the wording differs.

## Semantic Retrieval

A semantic retriever was implemented:

- Chunk embeddings
- Query embeddings
- Cosine similarity ranking
- Top-K retrieval

Architecture:

```text
Knowledge Base
      ↓
Chunking
      ↓
Embeddings
      ↓
Cosine Similarity
      ↓
Semantic Retrieval
      ↓
Top Results
```

Validation query:

```text
drug course length
```

Top result:

```text
antibiotics_guidelines.md
```

Similarity:

```text
0.4236
```

This was the first successful semantic retrieval test and demonstrated that embedding-based retrieval could solve problems that BM25 could not.

## Key Learning

Keyword retrieval answers:

```text
Do the words match?
```

Semantic retrieval answers:

```text
Do the meanings match?
```

This represented the transition from keyword search to semantic search.

---

# Most Important Learning

The biggest lesson was:

```text
Building AI applications is not just prompting.
```

Real AI systems require:
- orchestration
- validation
- frontend rendering
- confidence communication
- structured APIs
- UX interpretation
- state management
- debugging discipline

The project evolved from:

```text
“using AI”
```

to:

```text
“engineering AI workflows”
```

---

# Current Stage In Roadmap

Completed:

```text
[x] Basic Workflow System
[x] AI Orchestration Understanding
[x] Structured Extraction
[x] Confidence Handling
[x] Structured Rendering
[x] RAG Foundations
    - Knowledge Base
    - Loader
    - Chunking
    - Metadata
    - BM25 Retrieval
[x] Embeddings & Semantic Retrieval
    - Embeddings
    - Vector Representation
    - Cosine Similarity
    - Semantic Retrieval
```

Next phase:

```text
[ ] Vector Databases (FAISS)
[ ] Hybrid Retrieval
[ ] Agents
[ ] Enterprise Memory/Context
[ ] Multi-Step Orchestration
```

Vector Indexing & Scalable Retrieval

where the system moves from:

in-memory semantic retrieval

to:

high-performance vector indexing using FAISS.