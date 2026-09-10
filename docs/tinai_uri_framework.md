# Tinai-Uri annotation framework

## Scope and evidence standard

This policy is for Akam annotation. It is based on the Akattinai material of
Tolkappiyam/Porulatikaram and its scholarly transmission, not on a modern
emotion-label lookup. A record may receive a manual Tinai or Uri only with a
specific edition, commentary, or documented textual reasoning. Otherwise it
stays \`needs_review\`.

## Definitions

**Akam** is the interior/love-poetry mode; **Puram** is the exterior mode
associated with public, heroic, and kingly concerns. [Oxford’s account of
Sangam conventions](https://academic.oup.com/jaar/article-abstract/89/2/780/6287081)
supports this broad distinction.

**Tinai** is a conventional Akam poetic complex, not merely an emotion or a
physical landscape. It relates a setting to time, culturally associated
environmental markers and a human situation. The five corpus categories are
Kurinji, Mullai, Marutham, Neithal, and Palai. Scholarship describes the
system as correspondences between geography, mood and other markers, rather
than a simple equivalence. [Cambridge University Press](https://assets.cambridge.org/052185/6787/excerpt/0521856787_excerpt.pdf)

**Mutal-porul** denotes primary setting elements: land/place and time.
**Karu-porul** denotes the associated environmental and cultural material
(such as flora, fauna, occupations and local objects). **Uri-porul** is the
human behavioural/situational element that animates that conventional world.
[Asian Literature and Translation](https://alt.cardiffuniversitypress.org/articles/32/files/submission/proof/32-1-45-1-10-20181026.pdf)
describes this three-part analysis directly.

## Uri

The Tolkappiyam passage preserved in a Tamil Digital Library edition identifies
five uripporul categories: **punartal** (union/company), **pirital**
(separation), **iruttal** (remaining/waiting for return), **irankal**
(lamenting), and **utal** (love-quarrel), together with their causes.
[Tolkappiyam Porulatikaram edition](https://tamildigitallibrary.in/assets/docs/uploads/primary_files/book/TVA_BOK_0019423_Tolkappiyam_Porul_Atikaram.pdf)

These are controlled project-level Uri values only after a reviewer establishes
that the poem’s human action or circumstance supports one of them. They are
not automatic Tinai translations. Teaching shorthand that pairs a Tinai with
one typical situation may be useful for discovery, but it is insufficient as
poem-level proof; setting and karu can overlap and commentarial interpretation
can differ.

## Annotation procedure

1. Confirm Akam scope from the work and poem-level edition/commentary.
2. Record the source’s Tinai heading when present, but do not promote it beyond
   \`needs_review\` without independent review.
3. Assess mutal and karu as corroborating evidence, not as a keyword count.
4. Identify the represented human action/situation; assign a Uri only if a
   cited commentary or defensible close reading supports one of the five terms.
5. Put the exact citation, page/poem number, and any disagreement in
   \`annotation_notes\`; retain the pre-existing status workflow.

## Uncertainty and status

Conflicting commentary, mixed signals, truncated text, an absent source label,
or inability to distinguish an implied situation requires
\`annotation_status = needs_review\`. No automatic promotion is permitted.

## Source table

| Source | Type | What it supports | URL/reference |
|---|---|---|---|
| Tolkappiyam, Porulatikaram, Tamil Digital Library edition | Primary text with commentary/translation | Five uripporul terms; commentary notes interpretive issues | [PDF](https://tamildigitallibrary.in/assets/docs/uploads/primary_files/book/TVA_BOK_0019423_Tolkappiyam_Porul_Atikaram.pdf) |
| Iraiyanar Akapporul, Central Institute of Classical Tamil, 2012 | Classical Akam treatise, digital edition | Five Akam tinais and interpretive dimensions | [Catalogue](https://www.tamildigitallibrary.in/book-detail?id=jZY9lup2kZl6TuXGlZQdjZI8luYy&tag=Iraiyanar+akapporul+text%2C+transliteration+and+translations+in+english+verse+and+prose) |
| Asian Literature and Translation, 2018 | Peer-reviewed journal article | Mutal, karu and uri analytical distinction | [Article PDF](https://alt.cardiffuniversitypress.org/articles/32/files/submission/proof/32-1-45-1-10-20181026.pdf) |
| Cambridge University Press | Academic book excerpt | Tinai as landscape, mood and cultural correspondence | [Excerpt](https://assets.cambridge.org/052185/6787/excerpt/0521856787_excerpt.pdf) |
