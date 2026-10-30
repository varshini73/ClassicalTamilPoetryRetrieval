"""Build the combined Natrinai and Project Madurai Thirukkural corpus."""
from __future__ import annotations

import csv
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from unicodedata import normalize

ROOT = Path(__file__).resolve().parents[1]
NATRINAI_PATH = ROOT / "data" / "corpus" / "poetry_schema.csv"
COMBINED_PATH = ROOT / "data" / "corpus" / "combined_poetry_schema.csv"
RAW_PATH = ROOT / "data" / "raw" / "project_madurai_pm001_thirukkural.html"
SOURCES_PATH = ROOT / "data" / "raw" / "project_madurai_sources.json"
SOURCE_URL = "https://www.projectmadurai.org/pm_etexts/utf8/pmuni0001.html"
SOURCE_NAME = "Project Madurai Unicode Etext PM001"
COLOPHON_ENDING = "\u0bae\u0bc1\u0bb1\u0bcd\u0bb1\u0bbf\u0bb1\u0bcd\u0bb1\u0bc1"

FIELDS = ["collection", "poem_id", "work", "poem_number", "title", "section", "chapter_gloss_en", "poem_text", "akam_puram", "tinai", "uri", "emotion", "situation", "characters", "keywords", "source", "source_url", "translation", "annotation_notes", "annotation_status"]

# Standard English chapter titles with concise chapter-level discovery themes.
# These are retrieval aids only, not poem-level emotion or cultural annotations.
CHAPTER_GLOSSES_EN = (
    "The Praise of God: god, creation, worship, first cause", "The Blessing of Rain: rain, water, harvest, sustenance", "The Greatness of Ascetics: ascetics, virtue, discipline, spiritual strength", "The Power of Virtue: virtue, righteousness, moral strength, goodness", "Domestic Life: home, family, household, duty", "The Worth of a Wife: wife, marriage, household, partnership", "The Blessing of Children: children, parenthood, family, joy", "The Possession of Love: love, kindness, affection, compassion", "Hospitality: guests, welcome, generosity, hosting", "Sweet Speech: kind speech, courtesy, gentle words, respect",
    "Gratitude: gratitude, thanks, remembrance, kindness", "Impartiality: fairness, justice, equality, impartial judgment", "Self-Control: self control, restraint, discipline, conduct", "Good Conduct: conduct, ethics, virtue, proper behavior", "Not Coveting Another's Wife: fidelity, adultery, marriage, restraint", "Patience: patience, endurance, forgiveness, forbearance", "Freedom from Envy: envy, jealousy, contentment, goodwill", "Not Coveting: greed, coveting, contentment, desire", "Against Backbiting: backbiting, gossip, slander, speech", "Against Vain Speaking: idle talk, useless speech, silence, words",
    "Dread of Evil Deeds: wrongdoing, evil, consequences, conscience", "Knowledge of Duty: duty, righteousness, ethics, obligation", "Giving: charity, generosity, almsgiving, compassion", "Fame: reputation, honor, praise, lasting renown", "Compassion: compassion, mercy, kindness, empathy", "Abstinence from Flesh: nonviolence, meat, compassion, restraint", "Penance: penance, austerity, discipline, spiritual practice", "Inconsistent Conduct: hypocrisy, conduct, integrity, morality", "Absence of Fraud: honesty, fraud, deception, integrity", "Truthfulness: truth, honesty, speech, integrity",
    "Restraining Anger: anger, temper, rage, forgiveness, self control", "Non-injury: nonviolence, harm, compassion, kindness", "Not Killing: killing, life, nonviolence, mercy", "Instability: impermanence, change, mortality, uncertainty", "Renunciation: renunciation, detachment, asceticism, freedom", "Knowledge of Truth: truth, wisdom, knowledge, reality", "Eradication of Desire: desire, attachment, freedom, contentment", "Fate: fate, destiny, fortune, circumstance, providence", "The Greatness of a King: king, ruler, leadership, governance", "Learning: learning, education, study, wisdom",
    "Ignorance: ignorance, learning, knowledge, foolishness", "Hearing: listening, learning, counsel, wisdom", "The Possession of Knowledge: knowledge, wisdom, understanding, judgment", "Avoidance of Faults: faults, mistakes, conduct, self correction", "Seeking Aid: counsel, support, advisers, assistance", "Avoiding Mean Company: companions, friendship, character, association", "Acting after Due Consideration: deliberation, planning, action, judgment", "Knowing One's Strength: strength, capacity, limits, ability", "Knowing the Right Time: timing, opportunity, patience, action", "Knowing the Right Place: place, context, strategy, suitability",
    "Selection and Trust: choosing, trust, responsibility, people", "Testing and Trusting: testing, trust, character, selection", "Cherishing One's Kin: kin, relatives, family, support", "Unforgetfulness: memory, vigilance, responsibility, attention", "The Just Sceptre: justice, rule, king, fairness", "The Cruel Sceptre: tyranny, cruelty, rule, oppression", "Absence of Tyranny: oppression, justice, compassion, governance", "Benignity: kindness, mercy, ruler, compassion", "Spies: intelligence, spies, information, governance", "Energy: energy, effort, perseverance, action",
    "Unsluggishness: diligence, effort, laziness, industry", "Manly Effort: courage, effort, determination, achievement", "Not Being Dismayed by Trouble: adversity, courage, resilience, trouble", "Ministers: ministers, counsel, governance, advisers", "Eloquence: speech, eloquence, communication, persuasion", "Purity in Action: action, integrity, purity, conduct", "Firmness in Action: resolve, action, determination, perseverance", "The Manner of Action: method, action, planning, execution", "The Envoy: envoy, diplomacy, message, negotiation", "Conduct in the Presence of the King: king, court, conduct, caution",
    "Knowledge of Signs: signs, observation, insight, perception", "Knowledge of the Assembly: assembly, audience, speech, judgment", "Not Fearing the Assembly: courage, assembly, speech, confidence", "The Country: country, nation, people, prosperity", "Fortification: defense, fortress, security, protection", "Wealth: wealth, resources, prosperity, economy", "The Army: army, soldiers, strength, defense", "Military Pride: courage, honor, battle, warriors", "Friendship: friendship, loyalty, trust, companionship", "Testing Friendship: friendship, testing, loyalty, trust",
    "Old Friendship: old friends, loyalty, memory, companionship", "Harmful Friendship: harmful friends, betrayal, caution, association", "False Friendship: false friends, deception, friendship, caution", "Folly: folly, foolishness, error, judgment", "Ignorance: ignorance, foolishness, knowledge, learning", "Hostility: hostility, enemies, conflict, enmity", "The Might of Hatred: hatred, anger, enemies, conflict", "Knowing the Quality of Hate: hatred, enmity, discernment, conflict", "Internal Enmity: internal conflict, betrayal, enemies, caution", "Not Offending the Great: power, respect, offense, caution",
    "Being Led by Women: desire, infatuation, judgment, self control", "Wanton Women: desire, temptation, lust, restraint", "Not Drinking Liquor: alcohol, intoxication, self control, conduct", "Gambling: gambling, risk, loss, vice", "Medicine: health, illness, treatment, medicine", "Nobility: nobility, birth, character, honor", "Honour: honor, dignity, reputation, integrity", "Greatness: greatness, virtue, character, excellence", "Perfect Goodness: goodness, virtue, character, kindness", "Courtesy: courtesy, civility, manners, respect",
    "Useless Wealth: wealth, generosity, usefulness, selfishness", "Modesty: modesty, humility, shame, dignity", "Maintaining the Family's Excellence: family, duty, lineage, effort", "Agriculture: farming, agriculture, labor, food", "Poverty: poverty, hardship, need, suffering", "Begging: begging, poverty, charity, dignity", "Dread of Begging: begging, self respect, poverty, dignity", "Baseness: baseness, dishonor, conduct, dignity", "Fascination by Her Beauty: beauty, glance, captivation, infatuation, lovers", "Recognition of Signs: love, signs, lovers, recognition",
    "Rejoicing in Union: union, lovers, joy, embrace", "Praise of Her Beauty: beauty, beloved, love, admiration", "The Excellence of Love: love, affection, longing, lovers", "Abandonment of Reserve: love, reserve, confession, desire", "The Rumour: gossip, love, rumor, secrecy", "Separation Unendurable: separation, longing, lovers, grief", "Pining in Sorrow: grief, sorrow, pining, separation", "Eyes Wasting from Longing: eyes, tears, longing, separation", "The Pallor of Longing: pallor, sorrow, love, separation", "The Excess of Solitary Sorrow: loneliness, solitude, longing, grief",
    "Lamenting by Remembering: lament, memory, separation, longing", "Dream Visions: dreams, love, longing, imagination", "The Approach of Evening: evening, waiting, separation, longing", "Wasting Away: suffering, longing, love, separation", "Soliloquy: inner speech, longing, love, reflection", "The Loss of Reserve: reserve, loss, love, modesty", "Longing for the Beloved: longing, beloved, love, separation", "Reading the Signs: signs, love, feelings, lovers", "Desire for Reunion: reunion, love, longing, union", "Sulking with the Heart: sulking, heart, lovers, reproach",
    "Sulking: sulking, lovers, quarrel, reconciliation", "The Subtlety of Sulking: sulking, lovers, quarrel, suspicion", "The Joy of Reconciliation: joy, reconciliation, lovers, quarrel",
)
if len(CHAPTER_GLOSSES_EN) != 133:
    raise RuntimeError("Expected 133 English Thirukkural chapter glosses.")


def clean_lines(page: str) -> list[str]:
    page = re.sub(r"<br\s*/?>", "\n", page, flags=re.I)
    page = re.sub(r"</p\s*>", "\n", page, flags=re.I)
    page = re.sub(r"<[^>]+>", "", page)
    return [normalize("NFC", html.unescape(line).replace("\xa0", " ").strip()) for line in page.splitlines() if line.strip()]


def parse_thirukkural(page: str) -> list[dict[str, str]]:
    """Extract the numbered couplets and their source-supplied paal/chapter labels."""
    paal = chapter = ""
    records: list[dict[str, str]] = []
    verse_lines: list[str] = []
    started = False
    for line in clean_lines(page):
        if line.casefold().startswith("this page was first put up") or line.casefold().startswith("this unicode version") or line.casefold().startswith("please send your comments"):
            break
        if line.endswith(COLOPHON_ENDING):
            continue
        if re.fullmatch(r"[123]\.\s+.+", line):
            paal = re.sub(r"^[123]\.\s+", "", line)
            started = True
            continue
        if not started:
            continue
        if re.fullmatch(r"[123]\.\d+\.?\s+.+", line):
            chapter = re.sub(r"^[123]\.\d+\.?\s+", "", line)
            continue
        if re.fullmatch(r"[123]\.\d+\.\d+\.?\s+.+", line):
            # The source repeats the chapter heading before each block of ten.
            chapter = re.sub(r"^[123]\.\d+\.\d+\.?\s+", "", line)
            continue
        match = re.search(r"\s+(\d+)\s*$", line)
        if match and verse_lines:
            source_token = match.group(1)
            text = "\n".join([*verse_lines, line[:match.start()].rstrip()])
            number = len(records) + 1
            # PM001 contains inconsistent displayed numbers (including 7811 and
            # a shifted 1294); ordered couplets define the stable work id.
            records.append({"collection": "Thirukkural", "poem_id": f"TK{number:04d}", "work": "Thirukkural", "poem_number": str(number), "title": chapter, "section": paal, "chapter_gloss_en": CHAPTER_GLOSSES_EN[(number - 1) // 10], "poem_text": text, "akam_puram": "", "tinai": "", "uri": "", "emotion": "", "situation": "", "characters": "", "keywords": "", "source": SOURCE_NAME, "source_url": SOURCE_URL, "translation": "", "annotation_notes": "No Akam/Puram, Tinai, Uri, emotion, or situation annotation has been assigned.", "annotation_status": "needs_review"})
            verse_lines = []
            continue
        if line and not re.match(r"^(?:\d+\.){1,3}", line):
            verse_lines.append(line)
    if len(records) != 1330:
        raise ValueError(f"Expected 1330 Thirukkural couplets; extracted {len(records)}.")
    forbidden = ("this page was first put up", "this unicode version", "please send your comments")
    if any(any(marker in record["poem_text"].casefold() for marker in forbidden) or any(line.endswith(COLOPHON_ENDING) for line in record["poem_text"].splitlines()) for record in records):
        raise ValueError("Thirukkural extraction retained a colophon or page footer.")
    if len(records[-1]["poem_text"].splitlines()) != 2:
        raise ValueError("Kural 1330 must contain exactly its two source lines.")
    return records


def with_collection(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"collection": "Natrinai", "title": "", "section": "", "chapter_gloss_en": "", **row} for row in rows]


def main() -> int:
    try:
        if RAW_PATH.exists():
            page = RAW_PATH.read_text(encoding="utf-8")
        else:
            with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
                page = response.read().decode("utf-8")
        thirukkural = parse_thirukkural(page)
        with NATRINAI_PATH.open(encoding="utf-8-sig", newline="") as file:
            natrinai = list(csv.DictReader(file))
        if len(natrinai) != 399:
            raise ValueError(f"Expected 399 Natrinai records; found {len(natrinai)}.")
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Combined corpus build failed: {error}", file=sys.stderr)
        return 1
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not RAW_PATH.exists():
        RAW_PATH.write_text(page, encoding="utf-8")
    if not SOURCES_PATH.exists():
        SOURCES_PATH.write_text(json.dumps([{"collection": "Thirukkural", "source": SOURCE_NAME, "source_url": SOURCE_URL, "download_date": date.today().isoformat(), "raw_file": RAW_PATH.name}], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with COMBINED_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([*with_collection(natrinai), *thirukkural])
    print(f"Wrote {len(natrinai)} Natrinai and {len(thirukkural)} Thirukkural records to {COMBINED_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
