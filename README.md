# Culturally Grounded Retrieval of Classical Tamil Poetry from Modern Emotional Situations

## Run the working pilot

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## React + FastAPI application

The Streamlit pilot remains available as a fallback. The primary interface is
the React application, backed by FastAPI and the same Python retrieval module.

In one PowerShell terminal:

```powershell
cd C:\Users\VARSHINI\Desktop\ClassicalTamilPoetryRetrieval
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000
```

In a second PowerShell terminal:

```powershell
cd C:\Users\VARSHINI\Desktop\ClassicalTamilPoetryRetrieval\frontend
npm.cmd install
npm.cmd run dev -- --port 5173
```

Open `http://localhost:5173`. The API runs at `http://localhost:8000` and
exposes health, dataset-statistics, retrieval, and evaluation-query endpoints.

### Emotion model

The first backend stage uses `j-hartmann/emotion-english-distilroberta-base`
when available. Transformers caches its downloaded weights outside the
repository and runs inference on CPU. If packages, weights, or network access
are unavailable, the API explicitly returns the labelled rule-based fallback
and its reason rather than claiming a pretrained prediction.

The Streamlit application retrieves existing Natrinai records and preserves
their Tamil text and source links. It implements keyword matching, an offline
TF-IDF cosine-similarity fallback (not a pretrained sentence-embedding model),
emotion-aware reranking, and culturally grounded routing with optional
**user-supplied** Tinai/Uri constraints. Uri is never inferred from Tinai;
unresolved Uri rows remain eligible as a documented fallback.

`data/evaluation/modern_query_pilot.csv` contains six real-corpus candidate
sets for human relevance review. They are unreviewed, so the app does not
report definitive P@K, R@K, or MRR until explicit relevance judgments exist.

## Purpose

This research project will explore whether the traditional Akam/Puram–Tinai–Uri
structure can serve as an intermediate semantic routing layer between a modern
person's emotional situation and relevant Classical Tamil poetry.

## Current phase: Phase 1 — Corpus Schema & Annotation Framework Design

Phase 1 defines the corpus structure and a careful human annotation process.
It contains no collected poems, poem annotations, models, or retrieval system.

## Planned overall pipeline

```text
Modern user situation
  → Emotion/situation understanding
  → Akam/Puram
  → Tinai
  → Uri
  → Classical Tamil poetry retrieval
  → Simple Tamil/English explanation
```

The pilot will primarily focus on Akam poetry, while the schema supports both
Akam and Puram.

## Folder structure

```text
ClassicalTamilPoetryRetrieval/
├── data/
│   └── corpus/
│       └── poetry_schema.csv
├── docs/
│   ├── schema.md
│   ├── annotation_guidelines.md
│   └── annotation_workflow.md
├── scripts/
│   └── validate_schema.py
└── README.md
```

## Corpus

`data/corpus/poetry_schema.csv` is an empty, header-only corpus template. Each
future row will represent one poem or verse plus its source, traditional
literary metadata, and retrieval-oriented annotations. See
`docs/schema.md` for field definitions.

## Validate the schema

From the project root, run:

```powershell
python scripts/validate_schema.py
```

The script confirms the exact CSV columns, checks that populated `poem_id`
values are unique, and validates populated controlled fields. Blank annotation
fields are valid in Phase 1.

## Phase 2

Phase 2 will begin literature-grounded corpus preparation: sourcing poems,
recording provenance, and performing human draft annotations followed by
review and validation. The Uri taxonomy and traditional classifications must
first be verified against reliable Classical Tamil literary sources.

## Important restrictions

This phase does not implement poetry collection, actual poem annotation,
embeddings, semantic search, RAG, classifiers, query processing, a chatbot,
or explanation generation. Do not fabricate poems or literary annotations.
Any traditional Akam/Puram, Tinai, Uri, or character-role decision that
depends on scholarly interpretation requires human and literature-source
verification before use.
