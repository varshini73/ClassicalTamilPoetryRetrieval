"""Apply conservative draft annotations to Natrinai poems 1-50 only.

Evidence is the Project Madurai PM296 poem-level Tamil colophon already
preserved in annotation_notes. This is a reproducible draft overlay, not a
literary validation step.
"""
from __future__ import annotations
import csv
from pathlib import Path

FIELDS = ["uri", "emotion", "situation", "characters", "keywords", "annotation_status"]

# Only source-colophons that establish the human situation receive an Uri.
# Every other target is explicitly retained for later expert review.
A = {
 1: ("pirital","anxiety","A friend addresses a heroine who has understood that her lover may depart.","heroine, friend","anticipated separation, friend, lover","draft"),
 3: ("pirital","longing","A lover who previously left to seek wealth speaks to his heart about leaving again.","hero","separation, wealth, journey, lover","draft"),
 5: ("pirital","distress","A friend addresses a heroine distressed after learning of the hero's intended journey.","heroine, friend, hero","anticipated separation, journey, friend","draft"),
 7: ("pirital","distress","A friend addresses a heroine unable to bear the hero's departure in pursuit of wealth.","heroine, friend, hero","separation, wealth, departure, friend","draft"),
 8: ("punartal","love","After a natural union, the hero speaks on seeing the heroine with her companions.","hero, heroine, companions","union, meeting, lovers, companions","draft"),
 13: ("punartal","unease","After a natural union, a friend speaks to the heroine about her changed state.","heroine, friend, hero","union, friend, changed behaviour, lovers","draft"),
 16: ("pirital","resolve","The hero restrains his intended journey for wealth after confronting his heart's desire.","hero","separation, wealth, journey, resolve","draft"),
 18: ("pirital","distress","A friend consoles a heroine who cannot endure separation.","heroine, friend","separation, distress, consolation, friend","draft"),
 19: ("pirital","longing","A friend addresses a hero who united with and then left the heroine.","hero, heroine, friend","union, departure, separation, marriage","draft"),
 20: ("utal","anger","A heroine responds after the hero returns from another woman and denies involvement.","heroine, hero, other woman, friend","infidelity, estrangement, confrontation, jealousy","draft"),
 21: ("pirital","anticipation","A hero who has completed his task speaks to his charioteer while returning.","hero, charioteer","return, completed journey, separation, lover","draft"),
 24: ("pirital","acceptance","A heroine gladly tells a friend who has agreed to separation for the hero's pursuit of wealth.","heroine, friend, hero","separation, wealth, consent, friend","draft"),
 26: ("pirital","anxiety","A friend dissuades the hero from leaving after the heroine recognizes the impending separation.","heroine, friend, hero","anticipated separation, journey, anxiety, friend","draft"),
 28: ("pirital","distress","A friend addresses a heroine who cannot bear separation.","heroine, friend","separation, distress, friend","draft"),
 29: ("pirital","grief","A mother speaks after her daughter has gone away with the hero.","mother, heroine, hero","elopement, departure, mother, separation","draft"),
 30: ("utal","anger","A friend answers the hero after he returns from another woman and claims ignorance.","hero, friend, other woman","infidelity, estrangement, confrontation, friend","draft"),
 33: ("pirital","anxiety","A friend speaks to the hero after recognizing signs that the heroine has understood the planned separation.","heroine, friend, hero","anticipated separation, signs, anxiety, friend","draft"),
 37: ("pirital","longing","A friend speaks during separation after a promise or arrangement has been set.","friend, heroine, hero","separation, promise, longing, friend","draft"),
 39: ("punartal","love","The hero speaks at a subsequent meeting with the heroine.","hero, heroine","union, meeting, lovers","draft"),
 40: ("utal","estrangement","Another woman speaks while the heroine's close associate listens.","other woman, heroine, friend","other woman, estrangement, relationship conflict","draft"),
 41: ("pirital","distress","A friend consoles a heroine unable to bear an announced separation.","heroine, friend, hero","separation, consolation, distress, friend","draft"),
 42: ("pirital","anticipation","A hero who has completed his task speaks to his charioteer while returning.","hero, charioteer","return, completed journey, separation, lover","draft"),
 43: ("pirital","anxiety","A friend dissuades the hero from departing after separation has been announced.","hero, friend, heroine","anticipated separation, departure, friend, anxiety","draft"),
 44: ("punartal","anticipation","After confinement, the hero comes to the agreed meeting place and speaks.","hero, heroine","meeting, union, rendezvous, confinement","draft"),
 46: ("pirital","anxiety","A friend addresses the hero who has signalled separation.","hero, friend, heroine","anticipated separation, hero, friend, anxiety","draft"),
 48: ("pirital","anxiety","A friend addresses the hero who has signalled separation.","hero, friend, heroine","anticipated separation, hero, friend, anxiety","draft"),
 49: ("punartal","longing","A friend encourages the heroine toward a night meeting, while also remarking on her inability to endure.","heroine, friend, hero","night meeting, union, longing, friend","draft"),
}

def main():
    path = Path(__file__).resolve().parents[1] / "data" / "corpus" / "poetry_schema.csv"
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        rows = list(reader)
    for row in rows:
        number = int(row["poem_number"])
        if not 1 <= number <= 50:
            continue
        if "Batch 01 " in row["annotation_notes"]:
            continue
        prior = row["annotation_notes"].rstrip()
        if number in A:
            uri, emotion, situation, characters, keywords, status = A[number]
            row.update(dict(zip(FIELDS, (uri, emotion, situation, characters, keywords, status))))
            decision = f" Batch 01 draft: Uri '{uri}' and modern fields are conservative readings of the PM296 Tamil colophon; independent literary review is required."
        else:
            row["annotation_status"] = "needs_review"
            decision = " Batch 01 reviewed the PM296 Tamil colophon; it does not by itself establish a defensible controlled Uri, so Uri and modern interpretive fields remain blank pending specialist review."
        row["annotation_notes"] = prior + decision
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names); writer.writeheader(); writer.writerows(rows)
    target = sorted((row for row in rows if int(row["poem_number"]) <= 50), key=lambda row: int(row["poem_number"]))
    counts = {field: sum(bool(row[field]) for row in target) for field in ("uri", "emotion", "situation", "characters", "keywords")}
    statuses = {status: sum(row["annotation_status"] == status for row in target) for status in ("draft", "reviewed", "needs_review", "validated")}
    lines = [
        "# Annotation batch 01 report", "", "Batch: Natrinai 1-50", "",
        f"- Total poems: {len(target)}", f"- Uri assigned: {counts['uri']}",
        f"- Uri needs review: {len(target) - counts['uri']}",
        f"- Emotion assigned: {counts['emotion']}", f"- Situation assigned: {counts['situation']}",
        f"- Characters assigned: {counts['characters']}", f"- Keywords assigned: {counts['keywords']}",
        f"- Draft: {statuses['draft']}", f"- Reviewed: {statuses['reviewed']}",
        f"- Needs review: {statuses['needs_review']}", f"- Validated: {statuses['validated']}", "",
        "Evidence: target texts, poem numbers, Tinai headings, and Tamil colophons were previously checked against Project Madurai PM296. Draft annotations use only explicit colophon situations; Uri remains blank where that evidence is insufficient. No translation was added. The requested docs/verification_report.md is absent from this workspace.", "",
        "| Poem | Tinai | Uri | Emotion | Situation | Status | Evidence/Notes |",
        "|---:|---|---|---|---|---|---|",
    ]
    for row in target:
        situation = row["situation"].replace("|", "/") or "—"
        uri = row["uri"] or "—"; emotion = row["emotion"] or "—"
        evidence = "PM296 source colophon; " + ("draft close-reading" if row["uri"] else "insufficient Uri evidence")
        lines.append(f"| {row['poem_number']} | {row['tinai']} | {uri} | {emotion} | {situation} | {row['annotation_status']} | {evidence} |")
    report = Path(__file__).resolve().parents[1] / "docs" / "annotation_batch_01_report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Applied conservative batch-01 draft overlay: {len(A)} Uri assignments; {50-len(A)} needs-review records.")

if __name__ == "__main__":
    main()
