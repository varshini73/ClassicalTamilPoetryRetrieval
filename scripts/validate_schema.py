"""Validate the provenance-aware Classical Tamil corpus."""
import csv, sys
from collections import defaultdict
from pathlib import Path

COLUMNS = ["poem_id","work","poem_number","poem_text","akam_puram","tinai","uri","emotion","situation","characters","keywords","source","source_url","translation","annotation_notes","annotation_status"]
WORKS = {"Natrinai"}
AKAM_PURAM = {"Akam","Puram"}
TINAI = {"Kurinji","Mullai","Marutham","Neithal","Palai"}
URI = {"punartal","pirital","iruttal","irankal","utal"}
STATUSES = {"draft","reviewed","validated","needs_review"}

def main():
    path = Path(__file__).resolve().parents[1] / "data" / "corpus" / "poetry_schema.csv"
    errors, ids, pairs, texts = [], {}, {}, {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != COLUMNS:
                missing = [x for x in COLUMNS if x not in (reader.fieldnames or [])]
                extra = [x for x in (reader.fieldnames or []) if x not in COLUMNS]
                errors.append("Schema columns must exactly match the documented order. Missing: " + ", ".join(missing) + "; unexpected: " + ", ".join(extra))
                rows = []
            else: rows = list(reader)
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        print(f"Schema validation failed: {exc}"); return 1
    for n, row in enumerate(rows, 2):
        def value(k): return (row.get(k) or "").strip()
        for key in ("poem_id","work","poem_number","poem_text","source","source_url","annotation_status"):
            if not value(key): errors.append(f"Row {n}: {key} is required.")
        if value("work") and value("work") not in WORKS: errors.append(f"Row {n}: invalid work '{value('work')}'.")
        if value("akam_puram") and value("akam_puram") not in AKAM_PURAM: errors.append(f"Row {n}: invalid akam_puram.")
        if value("tinai") and value("tinai") not in TINAI: errors.append(f"Row {n}: invalid tinai.")
        if value("uri") and value("uri") not in URI: errors.append(f"Row {n}: invalid uri '{value('uri')}'.")
        if value("annotation_status") and value("annotation_status") not in STATUSES: errors.append(f"Row {n}: invalid annotation_status.")
        if value("poem_id") in ids: errors.append(f"Row {n}: duplicate poem_id {value('poem_id')} (row {ids[value('poem_id')]}).")
        ids[value("poem_id")] = n
        pair = (value("work"), value("poem_number"))
        if pair in pairs: errors.append(f"Row {n}: duplicate poem number {pair[1]} within {pair[0]}.")
        pairs[pair] = n
        canonical = " ".join(value("poem_text").split())
        if canonical in texts: errors.append(f"Row {n}: duplicate poem text (row {texts[canonical]}).")
        texts[canonical] = n
        if canonical.lower() in {"todo","tbd","placeholder","sample poem"}: errors.append(f"Row {n}: placeholder poem text.")
    if errors:
        print("Schema validation failed:"); print(*["- " + e for e in errors], sep="\n"); return 1
    print(f"Schema validation passed: {len(rows)} records in {path}"); return 0
if __name__ == "__main__": raise SystemExit(main())
