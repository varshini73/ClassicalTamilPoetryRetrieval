"""Conservative full-corpus Uri audit using explicit PM296 colophon wording.

This does not translate poems or create literary evidence. It assigns only when
the already-recorded Tamil colophon directly names a separation, union, or
quarrel situation; all remaining records are deliberately needs_review.
"""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path

URI_TERMS = {
    "pirital": ("பிரிவ",),
    "punartal": ("புணர்ச்சி",),
    "utal": ("ஊடல்",),
}
INTERPRETIVE_FIELDS = ("uri", "emotion", "situation", "characters", "keywords")

def decide(note: str) -> tuple[str, str]:
    # A mistress/other-woman reference alongside separation is not enough to
    # decide whether the poem's Uri is pirital or utal.
    if "பரத்தை" in note:
        return "", "The PM296 colophon includes an other-woman reference; Uri is ambiguous without commentary."
    hits = [uri for uri, terms in URI_TERMS.items() if any(term in note for term in terms)]
    if len(hits) == 1:
        return hits[0], f"The PM296 Tamil colophon explicitly contains the {hits[0]} situation term."
    if len(hits) > 1:
        return "", "The PM296 colophon contains more than one Uri-related term; specialist review is required."
    return "", "The PM296 colophon does not explicitly establish one controlled Uri; specialist review is required."

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    corpus = root / "data" / "corpus" / "poetry_schema.csv"
    with corpus.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file); fields = reader.fieldnames or []; rows = list(reader)
    for row in rows:
        for field in INTERPRETIVE_FIELDS:
            row[field] = ""
        note = row["annotation_notes"]
        uri, rationale = decide(note)
        row["uri"] = uri
        row["annotation_status"] = "draft" if uri else "needs_review"
        marker = " Full-corpus conservative audit:"
        existing = note.split(marker, 1)[0].rstrip()
        row["annotation_notes"] = existing + marker + " " + rationale
        if row["poem_number"] == "385":
            row["annotation_notes"] += " Source text is incomplete; no missing material was supplied."
    with corpus.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

    rows.sort(key=lambda row: int(row["poem_number"]))
    uri_counts = Counter(row["uri"] for row in rows if row["uri"])
    status_counts = Counter(row["annotation_status"] for row in rows)
    tinai_counts = Counter(row["tinai"] for row in rows)
    unresolved = [row for row in rows if not row["uri"]]
    report = [
        "# Natrinai annotation report", "", "## Corpus",
        f"- Total usable records: {len(rows)}", "- Works included: Natrinai",
        "- Missing poem number: 234 (excluded; uncertain reconstruction).",
        "- Source-incomplete poem: 385 (preserved as supplied; no missing text added).", "",
        "## Annotation counts",
        f"- Uri assigned: {sum(uri_counts.values())}", f"- Uri unresolved: {len(unresolved)}",
        "- Emotion assigned: 0", "- Situation assigned: 0", "- Characters assigned: 0", "- Keywords assigned: 0",
        f"- Reviewed: {status_counts['reviewed']}", f"- Needs review: {status_counts['needs_review']}", f"- Draft: {status_counts['draft']}", f"- Validated: {status_counts['validated']}", "",
        "## Tinai distribution",
    ]
    report += [f"- {name}: {tinai_counts[name]}" for name in ("Kurinji","Mullai","Marutham","Neithal","Palai")]
    report += ["", "## Uri distribution"] + [f"- {uri}: {uri_counts[uri]}" for uri in ("punartal","pirital","iruttal","irankal","utal")]
    report += ["", "## Methodology", "The PM296 poem-level Tamil colophon was re-audited for explicit controlled Uri wording only. Directly named separation, union, or quarrel terms receive a draft Uri. Indirect situations, conflicting signals, and absent direct terms remain needs_review. No Tinai-to-Uri mapping, translations, or inferred modern labels were used.", "", "## Sources", "- Project Madurai, Unicode Etext PM296 (row-level text, Tinai headings, and Tamil colophons).", "- The project Tinai-Uri framework and the cited Tolkappiyam/academic sources recorded there.", "", "## Uncertainty", "Every poem listed in natrinai_annotation_evidence.md with blank Uri requires specialist review; the common reasons are absent explicit Uri wording, indirect situation, or an other-woman reference that cannot safely distinguish pirital from utal."]
    (root / "docs" / "natrinai_annotation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    evidence = ["# Natrinai annotation evidence", "", "Source for every record: Project Madurai Unicode Etext PM296, using the row-level Tamil colophon already preserved in annotation_notes.", ""]
    for row in rows:
        confidence = "medium" if row["uri"] else "low"
        evidence += [f"## Poem: Natrinai {row['poem_number']}", f"- Tinai: {row['tinai']}", f"- Uri: {row['uri'] or 'unresolved'}", f"- Evidence: {row['annotation_notes'].split(' Full-corpus conservative audit:', 1)[-1].strip()}", "- Source: Project Madurai Unicode Etext PM296", f"- Confidence: {confidence}", ""]
    (root / "docs" / "natrinai_annotation_evidence.md").write_text("\n".join(evidence), encoding="utf-8")
    print(f"Audited {len(rows)} records: {sum(uri_counts.values())} draft Uri; {len(unresolved)} needs review.")

if __name__ == "__main__":
    main()
