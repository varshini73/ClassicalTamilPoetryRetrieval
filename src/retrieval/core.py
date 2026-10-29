from __future__ import annotations

import csv
import math
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .emotion_model import detect_pretrained_emotions

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "data" / "corpus" / "poetry_schema.csv"
TINAI = ("Kurinji", "Mullai", "Marutham", "Neithal", "Palai")
URI = ("punartal", "pirital", "iruttal", "irankal", "utal")
FIELDS = ("poem_text", "emotion", "situation", "characters", "keywords", "tinai", "uri")
STOPWORDS = {"a", "an", "and", "are", "but", "for", "i", "in", "is", "it", "my", "of", "on", "one", "or", "someone", "the", "them", "to", "we", "with", "you"}
EXPAND = {"separated":{"separation","departure","journey"}, "separation":{"departure","journey"}, "waiting":{"wait","return","longing"}, "return":{"waiting","journey"}, "love":{"lover","lovers","union"}, "conflict":{"quarrel","estrangement","anger"}, "secret":{"night","meeting","rendezvous"}, "longing":{"separation","distress","desire"}}
# These terms are meaningful to a reader but too general to rank a poem alone.
GENERIC_TERMS = {"love", "loved", "lover", "lovers", "union", "relationship", "friend", "hero", "heroine", "companions"}

# Transparent English cue inventory for the prototype.  Phrase cues have more
# weight than isolated tokens; "love" on its own is intentionally absent.
EMOTION_CUES = {
    "longing": (("miss", "long for", "yearn", "yearning", "waiting for", "far away"), {"miss", "waiting", "wait", "return", "far", "away"}),
    "sadness": (("sad", "unhappy", "heartbroken", "far away"), {"sad", "unhappy", "heartbroken", "lonely"}),
    "anxiety": (("worried", "anxious", "uneasy", "keep waiting"), {"worried", "anxious", "uneasy", "uncertain"}),
    "fear": (("afraid", "scared", "fear of", "might lose"), {"afraid", "scared", "fear", "lose"}),
    "joy": (("happy", "joyful", "so glad", "reunited"), {"happy", "joyful", "glad", "reunited"}),
    "anger": (("angry", "furious", "mad at", "conflict"), {"angry", "furious", "mad", "conflict"}),
    "jealousy": (("jealous", "betrayed", "other woman", "other man"), {"jealous", "betrayed"}),
    "hope": (("hope", "wish", "will return", "looking forward"), {"hope", "wish"}),
    "grief": (("grief", "grieving", "died", "loss"), {"grief", "grieving", "died", "loss"}),
    "desire": (("want to meet", "desire", "wish to meet", "secretly at night"), {"desire", "want", "meet"}),
    "uncertainty": (("not sure", "uncertain", "do not know", "maybe"), {"uncertain", "maybe"}),
}

def load_corpus(path=CORPUS_PATH):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 399:
        raise ValueError("Expected the 399-record Natrinai corpus.")
    return rows

def normalize(text):
    tokens = {x for x in re.findall(r"[\w\u0B80-\u0BFF]+", (text or "").casefold()) if x not in STOPWORDS and len(x) > 1}
    for token in tuple(tokens):
        tokens.update(EXPAND.get(token, set()))
    return sorted(tokens)

def submitted_sentences(query):
    """Return meaningful submitted sentences; one situation is accepted per search."""
    return [part.strip() for part in re.split(r"[.!?]+", query or "") if part.strip()]

def ensure_single_situation(query):
    sentences = submitted_sentences(query)
    if len(sentences) != 1:
        raise ValueError("Please submit one situation at a time; multiple sentences can describe different contexts.")
    return sentences[0]

def interpretation_value(value="", basis="", certainty="uncertain"):
    """A deliberately modest query-reading record, not a trained classifier."""
    return {"value": value, "basis": basis, "certainty": certainty}

def detect_rule_based_emotions(sentence):
    """Return sentence-level emotion cues for the untrained prototype.

    This is intentionally a rule baseline rather than an emotion classifier:
    it reports its exact matched cues and returns no primary label when no
    meaningful cue is present.  A generic relationship word never supplies a
    score by itself.
    """
    text = (sentence or "").casefold()
    tokens = set(normalize(sentence))
    scores, evidence = {}, {}
    for emotion, (phrases, words) in EMOTION_CUES.items():
        phrase_hits = [phrase for phrase in phrases if phrase in text]
        word_hits = sorted(words & tokens)
        score = 2 * len(phrase_hits) + len(word_hits)
        if score:
            scores[emotion] = score
            evidence[emotion] = {"phrases": phrase_hits, "words": word_hits}
    # "miss" plus a return/waiting context supports longing beyond one token.
    if "miss" in tokens and ({"waiting", "wait", "return", "far", "away"} & tokens):
        scores["longing"] = scores.get("longing", 0) + 1
    ordered = sorted(scores, key=lambda emotion: (-scores[emotion], emotion))
    primary = ordered[0] if ordered else ""
    secondary = ordered[1:3]
    confidence = "high" if primary and scores[primary] >= 3 else "moderate" if primary and scores[primary] >= 2 else "low" if primary else "uncertain"
    return {"method":"transparent rule-based baseline (not trained or validated)", "primary":primary, "secondary":secondary, "confidence":confidence, "confidence_label":"rule strength", "alternative_scores":scores, "evidence":evidence, "all_scores":scores, "model_name":"", "fallback_reason":""}

def detect_emotions(sentence):
    """Primary pipeline stage: cached pretrained model with disclosed fallback."""
    return detect_pretrained_emotions(sentence, detect_rule_based_emotions)

def contextual_interpretation(sentence):
    """Read explicit sentence cues that the seven-label model cannot express.

    This is deliberately a separate, non-numeric interpretation layer.  It
    never changes the pretrained model label or probability, and it is not
    used to infer a Tinai or Uri.
    """
    sentence = ensure_single_situation(sentence)
    terms, text = set(normalize(sentence)), sentence.casefold()
    relationship_language = bool({"love", "loved", "lover", "relationship", "partner"} & terms) or "loved one" in text
    if any(phrase in text for phrase in ("looking forward", "cannot wait", "can't wait", "expecting")) and relationship_language:
        return interpretation_value("anticipation", "explicit expectation language in a relationship context", "tentative")
    if ({"waiting", "wait", "return"} & terms) and relationship_language:
        return interpretation_value("longing", "waiting/return and relationship language", "tentative")
    if any(phrase in text for phrase in ("don't know", "do not know", "not sure", "uncertain", "unsure")):
        return interpretation_value("uncertainty", "explicit uncertainty language", "tentative")
    if ({"conflict", "quarrel", "troubled", "misunderstood", "misunderstanding", "betrayal", "estrangement"} & terms) and relationship_language:
        return interpretation_value("relationship distress", "relationship and conflict/misunderstanding language", "tentative")
    return interpretation_value(basis="No supported contextual interpretation was found in the sentence.")

def understand_situation(sentence):
    """Identify actions/events independently of detected emotion."""
    sentence = ensure_single_situation(sentence)
    terms, text = set(normalize(sentence)), sentence.casefold()
    if ({"waiting", "wait", "return"} & terms) and ({"love", "loved", "lover", "someone"} & terms or "someone" in text):
        return interpretation_value("waiting for a loved one's return", "waiting/return and relationship language", "tentative")
    if ({"afraid", "scared", "fear", "worried", "lose"} & terms) and ({"journey", "separation", "separated", "departure", "leave"} & terms):
        return interpretation_value("fear of separation during a journey", "fear plus journey/separation language", "tentative")
    if ({"journey", "separation", "separated", "departure", "leave"} & terms):
        return interpretation_value("separation during or before a journey", "journey/separation language", "tentative")
    if ({"secret", "night", "meeting", "meet", "rendezvous"} & terms) and ({"meet", "meeting", "rendezvous"} & terms):
        return interpretation_value("secret meeting at night", "meeting plus secrecy/night language", "tentative")
    if ({"conflict", "quarrel", "troubled", "betrayal", "estrangement", "misunderstood", "misunderstanding"} & terms):
        return interpretation_value("relationship conflict", "conflict/misunderstanding language", "tentative")
    if ({"meet", "meeting", "met", "reunited"} & terms) and ({"miss", "missed", "finally", "reunited"} & terms):
        return interpretation_value("reunion after separation", "meeting/reunion and prior-separation language", "tentative")
    if ({"afraid", "scared", "fear", "worried", "lose"} & terms) and ({"relationship", "love", "loved", "lover", "someone"} & terms or "someone" in text):
        return interpretation_value("fear of losing a relationship", "fear/loss and relationship language", "tentative")
    return interpretation_value(basis="No supported situation pattern was found in the sentence.")

def interpret_query(query, rows=None):
    """Extract transparent prototype cues without presenting them as scholarship.

    Uri is inferred from action words, never from Tinai.  A Tinai remains
    uncertain unless direct corpus evidence supports a later specialist review.
    """
    # Processing order is deliberate: emotion detection runs first, then an
    # independent action/situation pass, then cultural interpretation.
    query = ensure_single_situation(query)
    emotion_detection = detect_emotions(query)
    situation = understand_situation(query)
    contextual = contextual_interpretation(query)
    terms = set(normalize(query))
    text = query.casefold()
    relationship_words = {"love", "loved", "lover", "partner", "relationship"}
    has_relationship = bool(terms & relationship_words) or "loved one" in text
    domain = interpretation_value("Akam", "relationship/love language in the user situation", "tentative") if has_relationship else interpretation_value(basis="No clear Akam/Puram signal in the user text.")
    confidence = emotion_detection["confidence"]
    certainty = f"{confidence:.3f}" if isinstance(confidence, float) else confidence
    evidence = emotion_detection.get("evidence", {})
    cue_text = ", ".join(evidence.get(emotion_detection["primary"], {}).get("phrases", []) + evidence.get(emotion_detection["primary"], {}).get("words", []))
    emotion = interpretation_value(emotion_detection["primary"], ("Model prediction" if "pretrained" in emotion_detection["method"] else "Fallback cues") + (f": {cue_text}" if cue_text else ""), certainty)
    uri = interpretation_value()
    relationship = interpretation_value("lovers / intimate relationship", "relationship language in the user text", "tentative") if has_relationship else interpretation_value()
    if situation["value"] == "waiting for a loved one's return":
        uri = interpretation_value("iruttal", "waiting action is compatible with the controlled Uri term; requires literary review", "tentative")
    elif situation["value"] == "secret meeting at night":
        uri = interpretation_value("punartal", "meeting language is compatible with union/company; requires literary review", "tentative")
    elif situation["value"] == "relationship conflict":
        uri = interpretation_value("utal", "conflict language is compatible with the controlled quarrel term; requires literary review", "tentative")
    elif situation["value"] == "reunion after separation":
        uri = interpretation_value("punartal", "reunion/meeting language is compatible with the controlled union term; requires literary review", "tentative")
    elif situation["value"] in {"separation during or before a journey", "fear of separation during a journey"}:
        uri = interpretation_value("pirital", "separation/departure language is compatible with the controlled separation term; requires literary review", "tentative")
    # The project framework forbids a fixed Tinai-to-Uri mapping.  This pilot
    # consequently withholds a Tinai rather than pretending one follows.
    tinai = interpretation_value(basis="No automatic Tinai inference: a modern emotion/action does not establish a Tinai.")
    supported_uri = bool(rows and uri["value"] and any(row.get("uri") == uri["value"] for row in rows))
    routing = interpretation_value(uri["value"] if supported_uri else "", "The inferred Uri has corpus support." if supported_uri else "No matching reviewed/draft corpus Uri support; cultural filter will be relaxed.", "tentative" if supported_uri else "uncertain")
    notice = "Pretrained English emotion inference is used when available; it has seven labels and cannot directly identify longing or hope." if "pretrained" in emotion_detection["method"] else "Rule-based fallback is active because the pretrained model is unavailable; it is not a trained or validated cultural classifier."
    return {"processing_order":["emotion detection", "situation understanding", "contextual interpretation", "Akam/Puram interpretation", "candidate Tinai/Uri identification", "retrieval"], "emotion_detection":emotion_detection, "emotion": emotion, "contextual_interpretation": contextual, "situation": situation, "relationship": relationship, "domain": domain, "tinai": tinai, "uri": uri, "routing_uri": routing, "prototype_notice": notice}

def keyword_results(rows, query):
    query = ensure_single_situation(query)
    terms, weights, out = set(normalize(_vector_query(query))) - GENERIC_TERMS, {"keywords":4,"situation":3,"emotion":3,"characters":1,"poem_text":1,"tinai":1,"uri":2}, []
    for row in rows:
        evidence = {field: sorted(terms & set(normalize(row.get(field, "")))) for field in weights}
        evidence = {field: hits for field, hits in evidence.items() if hits}
        score = sum(weights[field] * len(hits) for field, hits in evidence.items())
        if score:
            out.append({"row":row,"score":float(score),"evidence":evidence,"explanation":"Matched " + "; ".join(f"{', '.join(v)} in {k}" for k,v in evidence.items()) + "."})
    return sorted(out, key=lambda x:(-x["score"], int(x["row"]["poem_number"])))

def _searchable_text(row):
    """Use poem content and retrieval annotations, excluding generic role labels."""
    fields = ("poem_text", "emotion", "situation", "keywords", "tinai", "uri")
    return " ".join(row.get(field, "") for field in fields)

def _vector_query(query):
    """Add independently detected situation terms, not an emotion-to-Tinai shortcut."""
    query = ensure_single_situation(query)
    situation = understand_situation(query).get("value", "")
    return " ".join((query, situation))

def _matching_evidence(row, query):
    terms = set(normalize(_vector_query(query))) - GENERIC_TERMS
    fields = ("situation", "keywords", "emotion", "uri", "tinai", "poem_text")
    evidence = {field: sorted(terms & (set(normalize(row.get(field, ""))) - GENERIC_TERMS)) for field in fields}
    return {field: hits for field, hits in evidence.items() if hits}

def vector_results(rows, query):
    query = ensure_single_situation(query)
    docs = [_searchable_text(row) for row in rows]
    # Use the project's normalizer for query and corpus so Tamil and English
    # token treatment is consistent and generic roles are not indexed.
    analyzer = lambda text: [term for term in normalize(text) if term not in GENERIC_TERMS]
    matrix = TfidfVectorizer(analyzer=analyzer).fit_transform(docs + [_vector_query(query)])
    scores, out = cosine_similarity(matrix[-1], matrix[:-1]).ravel(), []
    for row, score in zip(rows, scores):
        evidence = _matching_evidence(row, query)
        flattened = sorted({term for hits in evidence.values() for term in hits})
        explanation = "TF-IDF similarity; matching corpus evidence: " + "; ".join(f"{field}: {', '.join(hits)}" for field, hits in evidence.items()) if flattened else "TF-IDF similarity with no direct non-generic annotation overlap."
        out.append({"row":row,"score":float(score),"evidence":evidence,"explanation":explanation})
    return sorted(out, key=lambda x:(-x["score"], int(x["row"]["poem_number"])))

def emotion_results(rows, query, selected=""):
    detected = detect_emotions(query)
    mappings = {"longing":{"longing","desire","distress"}, "sadness":{"distress","grief"}, "anxiety":{"anxiety","distress"}, "fear":{"anxiety","distress"}, "joy":{"joy","love"}, "anger":{"anger","estrangement"}, "jealousy":{"jealousy","anger"}, "hope":{"joy","love"}, "grief":{"grief","distress"}, "desire":{"desire","love"}, "uncertainty":{"anxiety","distress"}}
    hints = {selected.casefold()} if selected else set().union(*(mappings.get(label, {label}) for label in [detected["primary"], *detected["secondary"]] if label))
    out = vector_results(rows, query)
    for item in out:
        label = item["row"].get("emotion", "").casefold()
        if label and label in hints:
            item["score"] += .35
            item["evidence"].setdefault("emotion", []).append(label)
            item["explanation"] += f" Emotion bonus: corpus label '{label}' matches detected sentence emotion."
        elif not label:
            item["explanation"] += " No emotion annotation: neither rewarded nor penalized."
    return sorted(out, key=lambda x:(-x["score"], int(x["row"]["poem_number"])))

def cultural_results(rows, query, tinai="", uri=""):
    interpretation = interpret_query(query, rows)
    routed_uri = uri or interpretation["routing_uri"]["value"]
    context = ["Akam scope (all Natrinai records in this pilot)", f"Tinai: {tinai} (advanced user constraint)" if tinai else interpretation["tinai"]["basis"], f"Uri routing: {routed_uri}" if routed_uri else interpretation["routing_uri"]["basis"]]
    out = vector_results(rows, query)
    for item in out:
        row, notes = item["row"], []
        if tinai and row["tinai"] == tinai: item["score"] += .45; notes.append("Tinai match")
        elif tinai: item["score"] -= .12; notes.append("different Tinai")
        if routed_uri and row["uri"] == routed_uri:
            item["score"] += .55
            item["evidence"].setdefault("uri", []).append(routed_uri)
            notes.append("Uri match")
        elif routed_uri and not row["uri"]: notes.append("Uri unresolved; retained without a routing bonus")
        elif routed_uri: item["score"] -= .18; notes.append("different Uri")
        item["explanation"] += " Cultural routing: " + (", ".join(notes) if notes else "no user constraint applied") + "."
    return sorted(out, key=lambda x:(-x["score"], int(x["row"]["poem_number"]))), context

def _meaningful_results(items):
    """Do not turn a stable tie of zero-score rows into apparent matches."""
    return [item for item in items if item["score"] > 0 and item.get("evidence")]

def _no_match_context(context):
    return [*context, "No strong corpus match: the query produced no positive score with supporting corpus evidence. Try a more specific situation or a different retrieval method."]

def retrieve(rows, model, query, emotion="", tinai="", uri="", limit=10):
    if model == "Keyword matching":
        context, results = ["Transparent lexical matching across text and populated annotations."], _meaningful_results(keyword_results(rows, query))
        return results[:limit], context if results else _no_match_context(context)
    if model == "Emotion-aware":
        context, results = ["Emotion-aware score; missing labels are not penalized."], _meaningful_results(emotion_results(rows, query, emotion))
        return results[:limit], context if results else _no_match_context(context)
    if model == "Culturally grounded routing":
        result, context = cultural_results(rows, query, tinai, uri)
        results = _meaningful_results(result)
        return results[:limit], context if results else _no_match_context(context)
    context, results = ["Offline TF-IDF cosine fallback. A sentence-embedding model is unavailable, so this is not claimed as embedding-based semantic retrieval."], _meaningful_results(vector_results(rows, query))
    return results[:limit], context if results else _no_match_context(context)

def corpus_statistics(rows):
    stats = {field:sum(bool(row.get(field, "").strip()) for row in rows) for field in ("emotion","situation","characters","keywords","uri")}
    stats.update({status:sum(row.get("annotation_status") == status for row in rows) for status in ("reviewed","draft","needs_review","validated")})
    return stats | {"records":len(rows)}

def metrics(rankings, judgments, k=5):
    eligible = [(qid, relevant) for qid, relevant in judgments.items() if relevant and qid in rankings]
    if not eligible: return {"precision_at_k":math.nan,"recall_at_k":math.nan,"mrr":math.nan,"queries":0}
    p = r = m = 0.0
    for qid, relevant in eligible:
        hits = [i for i, pid in enumerate(rankings[qid][:k], 1) if pid in relevant]
        p += len(hits)/k; r += len(hits)/len(relevant); m += 1/hits[0] if hits else 0
    n=len(eligible); return {"precision_at_k":p/n,"recall_at_k":r/n,"mrr":m/n,"queries":n}
