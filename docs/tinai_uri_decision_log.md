# Tinai-Uri decision log

| Decision | Basis and rationale | Consequence |
|---|---|---|
| Treat Tinai as a conventional complex, not an emotion label | Primary and academic sources link setting, time, karu and human situation | Do not infer Tinai from sadness, love, or a single nature word. |
| Use five Tolkappiyam uripporul labels as the initial controlled vocabulary | The checked Porulatikaram edition enumerates punartal, pirital, iruttal, irankal and utal | Uri remains blank unless poem-level evidence supports one label. |
| Do not encode a fixed Tinai-to-Uri lookup | The sources describe correspondences and acknowledge interpretive issues | A source Tinai heading does not automatically fill Uri. |
| Preserve source headings separately from independent validation | Project Madurai headings are edition evidence, not a second scholarly review | Existing rows remain needs_review. |

## Unresolved questions

- Which commentary/edition will be the preferred poem-level authority when
  commentators differ.
- How to cite line-level evidence consistently in the current CSV notes field.
- Whether a later pilot should distinguish the cause of an Uri from Uri itself.

## Full-corpus audit decision

The complete Natrinai audit uses only explicit Uri-related wording in the
PM296 poem-level colophon for a draft label: direct separation wording supports
pirital, explicit union wording supports punartal, and explicit quarrel wording
supports utal. Other wording, including travel, return, waiting, lament-like
language, and an other-woman reference, remains unresolved without poem-level
commentary because it cannot safely distinguish the controlled Uri categories.
This deliberately leaves many rows needs_review and does not assign modern
emotion, situation, character, or keyword fields.
