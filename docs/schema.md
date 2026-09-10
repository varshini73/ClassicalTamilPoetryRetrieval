# Corpus Schema — Classical Tamil Poetry Retrieval

## Phase 2 schema update

The live CSV now uses: `poem_id`, `work`, `poem_number`, `poem_text`,
`akam_puram`, `tinai`, `uri`, `emotion`, `situation`, `characters`,
`keywords`, `source`, `source_url`, `translation`, `annotation_notes`, and
`annotation_status`. Source-backed rows require nonempty poem ID, work, poem
number, poem text, source, source URL, and status. `needs_review` is a valid
additional status. `poem_number` preserves edition numbering; provenance,
translation, and notes preserve auditability.

## Purpose

This document defines every field in `data/corpus/poetry_schema.csv`. The corpus
stores one row per poem/verse and will later support retrieval from modern
free-text situations, routed through the traditional Akam/Puram–Tinai–Uri
poetic structure.

This is a SCHEMA DEFINITION document only. No poems, no classifications, no
embeddings exist yet. Population happens in Phase 2.

---

## Field Definitions

### poem_id
- **Purpose:** Unique identifier for each poem/verse row.
- **Format:** String, e.g. `KT_001` (work abbreviation + zero-padded number).
- **Required:** Yes, once a row is populated.
- **Allowed values:** Any unique string following the work's abbreviation
  convention. No fixed list — convention to be finalized per work when
  annotation begins (Phase 2).
- **Future retrieval use:** Primary key. Used to join this table against any
  future query-to-gold-poem evaluation dataset.

### work
- **Purpose:** Name of the source anthology/text the poem belongs to
  (e.g. Kurunthogai, Natrinai, Akananuru, Ainkurunuru, Purananuru).
- **Format:** String, canonical work name.
- **Required:** Yes, once populated.
- **Allowed values:** Not fixed at schema stage — REQUIRES
  LITERATURE-SOURCE VERIFICATION before a canonical list is finalized,
  since spelling/transliteration conventions vary by source (e.g.
  "Kurunthogai" vs "Kuruntokai").
- **Future retrieval use:** Allows filtering/reporting retrieval results by
  source anthology; needed since Akam and Puram works differ structurally
  in how tinai/uri apply.

### poem_text
- **Purpose:** The original Classical Tamil verse text, exactly as sourced.
- **Format:** String, Unicode Tamil.
- **Required:** Yes, once populated.
- **Allowed values:** N/A (free text, verbatim from a cited source).
- **Future retrieval use:** The literary object actually retrieved and shown
  to the user; also the eventual input to any simple-Tamil/English
  explanation layer (a later phase, out of scope for Phase 1).

### akam_puram
- **Purpose:** Classifies the poem under the two broad traditional divisions
  of Sangam-era Tamil poetry.
- **Format:** String, controlled vocabulary.
- **Required:** Optional at this phase (populated during annotation, not
  schema design).
- **Allowed values:** `Akam` | `Puram`
- **Future retrieval use:** This is the FIRST branch point in the retrieval
  routing pipeline. Puram poems (kingship, war, public ethics) do not use
  the Akam tinai/uri framework the same way Akam poems (love, personal/
  domestic life) do. A situation classified as Puram-type must be routed
  differently downstream from an Akam-type situation. This branching
  requirement REQUIRES LITERATURE-SOURCE VERIFICATION on exactly how
  Puram poems should be handled when tinai/uri do not cleanly apply —
  this is a known open design question, not yet resolved, and must not be
  papered over during annotation.

### tinai
- **Purpose:** Classifies an Akam poem by its traditional landscape/emotional
  setting.
- **Format:** String, controlled vocabulary.
- **Required:** Conditionally optional — expected to be populated only when
  `akam_puram = Akam`. Should remain blank for Puram poems unless a cited
  source explicitly assigns a tinai-equivalent category to a Puram poem
  (rare; verify before assigning).
- **Allowed values:** `Kurinji` | `Mullai` | `Marutham` | `Neithal` | `Palai`
- **Future retrieval use:** Second branch point in routing. Determines which
  landscape-associated subset of the corpus a matched situation is routed
  toward before uri-level matching and semantic reranking.

### uri
- **Purpose:** The specific emotional/situational state traditionally
  associated with a tinai (e.g. union, waiting, separation, patient waiting,
  quarrel/estrangement — exact terms and their precise scope differ by
  tinai and by traditional source).
- **Format:** String, free text at this stage.
- **Required:** Optional at this phase.
- **Allowed values:** NOT FIXED. Do not invent a taxonomy here. The final
  set of uri categories per tinai will be established during
  literature-grounded annotation preparation (Phase 2), by consulting
  authoritative sources on Sangam poetics (e.g. Tolkappiyam's Porulatikaram,
  and secondary scholarly literature) before any category list is locked in.
  Any uri value entered before that verification step must be treated as
  provisional and re-checked, not authoritative.
- **Future retrieval use:** Third and finest-grained branch point in routing
  — the layer intended to most closely match a modern situation's emotional
  specificity (e.g. "waiting for someone who may not return" maps to a
  specific uri, not just a tinai).

### emotion
- **Purpose:** A modern, plain-language emotional label for the poem's
  content (e.g. longing, grief, anxiety, joy) — distinct from `uri`.
- **Format:** String, free text or short tag(s).
- **Required:** Optional at this phase.
- **Allowed values:** Not fixed. This field is deliberately NOT a
  traditional literary category — see `annotation_guidelines.md` for the
  explicit distinction between this field and `uri`.
- **Future retrieval use:** Supports the "emotion-aware retrieval" baseline
  model (Model 3 in the planned evaluation), which is a comparison point
  against the proposed tinai/uri-routed method (Model 4), not the same
  mechanism.

### situation
- **Purpose:** A modern, plain-language description of the real-world
  scenario the poem's content resembles or could be matched to
  (e.g. "lovers separated by distance," "a friend's betrayal").
- **Format:** String, free text.
- **Required:** Optional at this phase.
- **Allowed values:** Not fixed; free text.
- **Future retrieval use:** Human-readable bridge between a modern user
  query and the poem's traditional classification — used both for
  annotation sanity-checking and potentially as training/reference text for
  the situation-understanding step of the pipeline.

### characters
- **Purpose:** The traditional character roles present in the poem, where
  applicable (Akam poetry uses a fixed set of conventional character roles,
  e.g. thalaivan/hero, thalaivi/heroine, thozhi/confidante).
- **Format:** String, comma or pipe-separated list.
- **Required:** Conditionally optional — expected only for Akam poems.
  REQUIRES LITERATURE-SOURCE VERIFICATION for the complete and correctly
  spelled set of traditional character-role terms before this field is
  populated at scale.
- **Allowed values:** Not fixed pending verification above.
- **Future retrieval use:** Potential future filter/context signal; not
  required for the core Phase 1–era routing logic.

### keywords
- **Purpose:** Free-text searchable terms associated with the poem's content
  (e.g. "separation," "waiting," "rain," "seashore").
- **Format:** String, comma or pipe-separated list.
- **Required:** Optional.
- **Allowed values:** Not fixed; free text.
- **Future retrieval use:** Supports the keyword-matching baseline model
  (Model 1 in the planned evaluation).

### annotation_status
- **Purpose:** Tracks the review state of the row, controlling whether it
  may be used as gold-standard evaluation data.
- **Format:** String, controlled vocabulary.
- **Required:** Yes, once a row exists (defaults to `draft` on creation).
- **Allowed values:** `draft` | `reviewed` | `validated`
- **Future retrieval use:** Only `validated` rows should be used for
  reporting evaluation results. See `annotation_workflow.md` for the full
  promotion process. No row should be auto-promoted past `draft`.

---

## Summary distinction (important — read before annotating)

- `akam_puram`, `tinai`, `uri` = **traditional literary classification**,
  grounded in citable Sangam-poetics scholarship. These require
  literature-source verification and must not be guessed or inferred purely
  from a modern reading of the poem.
- `emotion`, `situation` = **modern interpretive labels**, written in plain
  language by an annotator, used for retrieval matching and as reference
  text — not claims about traditional classification.
- `characters`, `keywords` = **supporting metadata**, partly traditional
  (characters) and partly free-text (keywords).

Conflating the traditional layer with the modern interpretive layer is a
known risk for this project and must be avoided at both the schema and
annotation level.
