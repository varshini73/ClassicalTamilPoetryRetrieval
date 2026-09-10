# Culturally Grounded Retrieval of Classical Tamil Poetry from Modern Emotional Situations

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
