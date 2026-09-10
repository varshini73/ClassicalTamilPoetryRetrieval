# Annotation Guidelines — Classical Tamil Poetry Retrieval

## Purpose

Practical guidance for human annotators populating the corpus defined in
`schema.md`. This document does not itself assert literary classifications —
it explains HOW to annotate correctly and cautiously, and where a cited
source is required before a value can be entered.

---

## 1. Akam / Puram

**What it is:** The primary traditional division of Sangam-era Tamil poetry
into Akam (interior/personal life — primarily love and relationships) and
Puram (exterior/public life — primarily kingship, war, ethics, and heroism).

**How to annotate:**
- Determine this from the poem's actual subject matter and, where available,
  from how the poem is classified in its source anthology or by its
  traditional commentary — not from a quick personal impression of "does
  this feel romantic or heroic."
- If the source anthology itself is conventionally understood as one
  category throughout (e.g. Purananuru is conventionally Puram-focused,
  Kurunthogai conventionally Akam-focused), that is a starting signal, not
  a substitute for checking the individual poem — exceptions exist and
  must be checked, not assumed away.
- If genuinely uncertain, do not guess. Mark `annotation_status = draft` and
  leave a note for a second reviewer rather than forcing a value.

**Do not:** invent a middle category. If a poem does not clearly fit either,
flag it for review rather than picking one arbitrarily.

## 2. Tinai

**What it is:** For Akam poems, the traditional landscape-based category
(Kurinji, Mullai, Marutham, Neithal, Palai), each traditionally associated
with a geographic landscape and a corresponding emotional/relational phase.

**How to annotate:**
- Only assign a tinai when `akam_puram = Akam`.
- Base the assignment on the poem's actual landscape imagery and situational
  content (e.g. mountains and union → Kurinji; forest/pastoral and patient
  waiting → Mullai), cross-checked against a cited traditional or scholarly
  source — REQUIRES LITERATURE-SOURCE VERIFICATION, especially for poems
  that mix landscape imagery or are ambiguous.
- If a traditional commentary or scholarly classification already assigns a
  tinai to this specific poem, cite that source directly rather than
  re-deriving it from scratch.
- Leave blank and flag for review if the poem does not clearly signal one
  landscape category.

**Do not:** assign a tinai based on modern intuition about which landscape
"feels right" without checking the poem's actual imagery and a cited source.

## 3. Uri

**What it is:** The specific traditional emotional/relational state
associated with a tinai (e.g. union, separation, patient waiting,
estrangement — the exact vocabulary and scope vary by source and must be
verified, not assumed).

**How to annotate:**
- Do NOT annotate this field freely until a verified uri taxonomy (per
  tinai) has been established from an authoritative source (see
  `schema.md` — this is explicitly deferred to literature-grounded
  preparation before bulk annotation begins).
- Any early/pilot uri annotation must cite the specific source consulted
  and should be treated as provisional (`draft`) until cross-checked.
- Once a verified taxonomy exists, annotate by matching the poem's content
  to the closest defined uri category for its tinai — not by inventing a
  new label on the spot.

**Do not:** treat `uri` as a free creative label. It is a traditional
technical term with a specific scope; using it loosely defeats the purpose
of grounding retrieval in the traditional structure.

## 4. Emotion

**What it is:** A modern, plain-language emotional description of the
poem's content — this is an interpretive/retrieval-support field, NOT a
traditional classification.

**How to annotate:**
- Write in your own words what emotion(s) the poem conveys to a modern
  reader (e.g. "longing," "grief," "quiet joy").
- This can and often will differ in vocabulary from the traditional `uri`
  term for the same poem — that is expected and fine. Do not force them to
  match; they serve different purposes (see `schema.md` summary section).
- Multiple emotions may be listed if genuinely present; avoid vague
  catch-alls like "sad" when a more specific term is available.

**Do not:** treat this as equivalent to or a translation of `uri`. Conflating
the two is a known risk for this project.

## 5. Situation

**What it is:** A modern, plain-language description of the real-world
scenario the poem resembles.

**How to annotate:**
- Write a short, concrete situation sentence (e.g. "A person waits for a
  loved one who has traveled far away and may not return").
- Base this directly on the poem's actual content, not on a generic
  paraphrase of the tinai/uri category.
- This field is meant to be usable later as a bridge to real user queries —
  write it the way an actual person describing their own situation might.

**Do not:** copy the tinai or uri label as the situation text; situation
should read like a real-life sentence, not a category name.

## 6. Characters

**What it is:** The conventional character roles present in an Akam poem
(e.g. hero, heroine, confidante — exact traditional terms REQUIRE
LITERATURE-SOURCE VERIFICATION before this field is populated at scale).

**How to annotate:**
- Only populate for Akam poems where character roles are clearly identifiable
  from the poem or its traditional commentary.
- Use the verified traditional terms once established; do not invent
  English approximations as a substitute for the correct Tamil terms.
- Leave blank and flag for review if character roles are ambiguous or the
  correct terminology has not yet been verified.

**Do not:** populate this field before the terminology verification step
described in `schema.md` is complete.

## 7. Keywords

**What it is:** Free-text searchable terms describing concrete content in
the poem (objects, imagery, themes).

**How to annotate:**
- List concrete nouns/themes actually present in the poem (e.g.
  "seashore," "rain," "waiting," "mountain path").
- Keep terms short and search-friendly; avoid full sentences here (use
  `situation` for that).

**Do not:** use this field for emotional labels — that belongs in `emotion`.

---

## General rule across all fields

If you are not confident a value is correct, do not fill it in to make the
row look complete. An honest blank field with `annotation_status = draft`
is more useful to the project than a confident-looking but unverified value.

## Tinai-Uri policy for subsequent annotation

Follow docs/tinai_uri_framework.md and record poem-level evidence in
annotation_notes. Treat Tinai as the conventional Akam complex of mutal
(place/time), karu (associated environment), and uri (human situation), not as
a one-word emotion. Do not derive Uri from Tinai alone.

The initial approved Uri vocabulary is punartal, pirital, iruttal, irankal,
and utal, but a label is permitted only when evidence supports that poem-level
reading. Conflicting sources, incomplete text, or insufficient evidence require
needs_review. The existing draft -> reviewed -> validated human workflow
remains mandatory; no source heading or automated extraction may validate a row.

## Corpus-wide colophon limitation

For Natrinai, Project Madurai PM296 colophons may directly name a separation,
union, or quarrel situation and can support a draft Uri label when the wording
is unambiguous. They are not a substitute for a commentary or translation. Do
not infer emotion, situation, characters, or keywords at scale from a Tinai
heading or from indirect colophon wording; leave those fields blank and use
needs_review until a poem-level scholarly review is available.
