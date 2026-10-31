# Annotation Workflow — Classical Tamil Poetry Retrieval

## Purpose

Defines the review lifecycle every corpus row moves through, and how
uncertain or contested annotations are handled. This governs the
`annotation_status` field defined in `schema.md`.

---

## The three states

### `draft`
- Default state for any newly created or newly annotated row.
- Includes: initial human annotation, any AI/LLM-assisted first-pass
  annotation, or partially completed rows.
- A `draft` row may contain blank optional fields — this is expected and
  acceptable at this stage, not an error.
- **A `draft` row must never be used as gold-standard/evaluation data.**

### `reviewed`
- A human annotator (not necessarily the original annotator) has checked
  the row against cited sources — traditional commentary for
  `akam_puram`/`tinai`/`uri`/`characters`, and the poem's own content for
  `emotion`/`situation`/`keywords` — and corrected any errors found.
- All literary-classification fields (`akam_puram`, `tinai`, `uri`,
  `characters`) that are populated at this stage must have a traceable
  source justification, even if that justification lives in a separate
  annotation-notes record rather than in this schema's fields directly.
- Moving a row to `reviewed` is a deliberate action by a human reviewer —
  never automatic, and never performed by the same pass that created the
  `draft` annotation without a distinct review step.

### `validated`
- A second, independent reviewer — ideally someone with stronger
  literary/Tamil-poetics background than the first reviewer — has
  independently confirmed the row without simply deferring to the first
  reviewer's judgment.
- Only `validated` rows may be used for reporting evaluation results,
  building the gold-standard query-to-poem dataset, or making claims about
  corpus content in written project outputs.

---

## Handling uncertainty

- If a reviewer is unsure whether a value is correct, the row **stays at
  its current status** (does not advance) and the uncertainty is recorded
  for follow-up — it is not resolved by guessing to keep the pipeline
  moving.
- If two reviewers disagree during the `reviewed → validated` step, the
  row does not become `validated` until the disagreement is resolved by
  consulting an additional source or a third opinion. A disagreement is
  not settled by majority vote of confidence alone.
- Fields explicitly marked in `schema.md` as "REQUIRES
  LITERATURE-SOURCE VERIFICATION" (e.g. canonical work-name spellings, the
  uri taxonomy, character-role terminology) must not be populated with
  provisional values at the `reviewed` or `validated` stage — provisional
  values belong only in `draft`.

## Hard rule on automation

**No row may be automatically promoted from `draft` to `reviewed` or
`validated`, regardless of the confidence or fluency of the annotation —
including AI/LLM-generated annotation.** Promotion requires a distinct,
deliberate human review action at each step. This applies even when an
annotation looks correct and well-formed; fluency is not evidence of
accuracy, particularly for a low-resource, classical-language domain where
models are prone to confident but ungrounded output.

## Row lifecycle example

```
1. Annotator proposes akam_puram, tinai, uri,
   emotion, situation, characters, keywords for a poem.
   -> annotation_status = draft

2. A human reviewer checks each literary-classification field against a
   cited source, corrects errors, and confirms modern-interpretive fields
   are reasonable and non-conflated with traditional fields.
   -> annotation_status = reviewed

3. A second, independent reviewer checks the row without simply trusting
   the first reviewer's conclusions, and confirms.
   -> annotation_status = validated
```

Only rows that complete all three steps may be used in Phase 2 corpus
statistics, Phase 2+ evaluation datasets, or any written results.
