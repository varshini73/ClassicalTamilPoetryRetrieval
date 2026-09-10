"""Build a provenance-first Natrinai corpus from its Project Madurai edition."""
from __future__ import annotations
import csv, html, re, sys, urllib.request
from pathlib import Path
from unicodedata import normalize

SOURCE_NAME = "Project Madurai Unicode Etext PM296"
SOURCE_URL = "https://www.projectmadurai.org/pm_etexts/utf8/pmuni0296.html"
TINAI_MAP = {
    "\u0b95\u0bc1\u0bb1\u0bbf\u0b9e\u0bcd\u0b9a\u0bbf": "Kurinji",
    "\u0bae\u0bc1\u0bb2\u0bcd\u0bb2\u0bc8": "Mullai",
    "\u0bae\u0bb0\u0bc1\u0ba4\u0bae\u0bcd": "Marutham",
    "\u0ba8\u0bc6\u0baf\u0bcd\u0ba4\u0bb2": "Neithal",
    "\u0baa\u0bbe\u0bb2\u0bc8": "Palai",
}
FIELDS = ["poem_id","work","poem_number","poem_text","akam_puram","tinai","uri","emotion","situation","characters","keywords","source","source_url","translation","annotation_notes","annotation_status"]

def clean_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</p\s*>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return normalize("NFC", "\n".join(line for line in (html.unescape(x).strip() for x in fragment.splitlines()) if line))

def parse_records(page: str) -> list[dict[str, str]]:
    tinai_names = "|".join(TINAI_MAP)
    header = re.compile(r"<p>\s*(?P<number>\d+)\s+(?P<heading>[^<]*)(?P<body>.*?)(?=<p>\s*\d+\s+[^<]*(?=<)|</body>)", re.I | re.S)
    records = []
    for match in header.finditer(page):
        number, body = int(match["number"]), match["body"]
        tinai_raw = next((name for name in TINAI_MAP if name in match["heading"]), None)
        note_match = re.search(r"<small>(.*?)</small>", body, re.I | re.S)
        poem_text = clean_html(body[:note_match.start()] if note_match else body)
        note = clean_html(note_match.group(1)) if note_match else ""
        if not poem_text and number == 234:
            # The source itself identifies 234 as uncertain and supplies no verse text.
            continue
        if not poem_text: raise ValueError(f"Poem {number} has no extracted text.")
        annotation_note = "Tinai and note are transcribed from the Project Madurai edition; independent scholarly review is still required."
        if note: annotation_note += " Source-supplied Tamil note: " + note
        if tinai_raw is None:
            annotation_note += " No Tinai label was machine-detected in this source heading; leave blank pending human review."
        records.append({"poem_id":f"NT{number:03d}","work":"Natrinai","poem_number":str(number),"poem_text":poem_text,"akam_puram":"Akam","tinai":TINAI_MAP[tinai_raw] if tinai_raw else "","uri":"","emotion":"","situation":"","characters":"","keywords":"","source":SOURCE_NAME,"source_url":SOURCE_URL,"translation":"","annotation_notes":annotation_note,"annotation_status":"needs_review"})
    expected_numbers = set(range(1,401)) - {125, 201, 234}
    if len(records) != 397 or {int(r["poem_number"]) for r in records} != expected_numbers:
        raise ValueError(f"Expected 397 available poem records; extracted {len(records)}.")
    return records

def main() -> int:
    target = Path(__file__).resolve().parents[1] / "data" / "corpus" / "poetry_schema.csv"
    try:
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response: records = parse_records(response.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Corpus build failed: {error}", file=sys.stderr); return 1
    with target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS); writer.writeheader(); writer.writerows(records)
    print(f"Wrote {len(records)} Natrinai records to {target}"); return 0
if __name__ == "__main__": raise SystemExit(main())
