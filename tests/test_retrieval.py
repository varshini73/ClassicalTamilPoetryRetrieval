import os
from pathlib import Path
import pytest

os.environ["CLASSICAL_TAMIL_EMOTION_FORCE_FALLBACK"] = "1"
os.environ["CLASSICAL_TAMIL_SEMANTIC_DISABLE"] = "1"

from fastapi import HTTPException
from api import RetrieveRequest, search, serialize
from src.retrieval.core import MEANING_DEFAULTS, _mark_semantic_weak_matches, auto_results, contextual_interpretation, cultural_results, detect_emotions, detect_rule_based_emotions, hybrid_results, interpret_query, keyword_results, load_corpus, load_curated_meanings, load_meanings, load_natrinai_corpus, metrics, ndcg_at_k, retrieve, semantic_results, vector_results
from src.retrieval.semantic_model import ALLOW_DOWNLOAD_ENV, CACHE_ENV, DISABLE_ENV, SemanticModelUnavailable, corpus_embeddings, get_semantic_model
from src.retrieval.emotion_model import MODEL_NAME, format_pretrained_output

def test_corpus_loads():
    rows = load_corpus()
    assert len(rows) == 1729
    assert all(r["poem_text"] and r["source_url"] for r in rows)
    assert {row["collection"] for row in rows} == {"Natrinai", "Thirukkural"}

def test_natrinai_source_rows_are_preserved_in_the_combined_corpus():
    original = load_natrinai_corpus()
    combined = [row for row in load_corpus() if row["collection"] == "Natrinai"]
    assert len(original) == len(combined) == 399
    assert [{key: row[key] for key in row} for row in original] == [{key: row[key] for key in original[0]} for row in combined]

def test_cultural_routing_does_not_apply_to_non_akam_collections():
    thirukkural = next(row for row in load_corpus() if row["collection"] == "Thirukkural")
    results, context = cultural_results([thirukkural], "separation", tinai="Palai", uri="pirital")
    assert "non-Akam collections receive no Tinai/Uri routing" in context[0]
    assert "not applied because this collection is not annotated as Akam" in results[0]["explanation"]
    assert "Tinai match" not in results[0]["explanation"]

def test_thirukkural_chapter_glosses_support_english_discovery_without_cultural_labels():
    rows = [row for row in load_corpus() if row["collection"] == "Thirukkural"]
    assert len(rows) == 1330 and all(row["chapter_gloss_en"] for row in rows)
    assert all(not row["tinai"] and not row["uri"] for row in rows)
    assert keyword_results(rows, "anger")[0]["row"]["poem_id"].startswith("TK")

def test_keyword_ranking():
    result = keyword_results(load_corpus(), "separation journey")
    assert result and result[0]["score"] > 0
    assert result[0]["row"]["poem_id"].startswith("NT")

def test_cultural_routing():
    result, context = cultural_results(load_corpus(), "separation", tinai="Palai", uri="pirital")
    assert result and any("Tinai match" in x["explanation"] for x in result)
    assert any("Uri routing: pirital" in x for x in context)
    assert any(not x["row"]["uri"] for x in result)

def test_metrics():
    assert metrics({"q1":["NT001","NT002"]}, {"q1":{"NT001"}}, 2) == {"precision_at_k":.5,"recall_at_k":1.0,"mrr":1.0,"queries":1}
    assert ndcg_at_k({"q1":["NT001","NT002"]}, {"q1":{"NT001": 2}}, 2) == {"ndcg_at_k":1.0,"queries":1}
    assert metrics({}, {}, 5)["queries"] == 0

def test_query_interpretation_is_tentative_and_never_derives_tinai_from_uri():
    interpretation = interpret_query("I am waiting for someone I love to return", load_corpus())
    assert interpretation["domain"]["value"] == "Akam"
    assert interpretation["uri"]["value"] == "iruttal"
    assert interpretation["tinai"]["value"] == ""
    assert interpretation["routing_uri"]["value"] == ""  # no corpus iruttal annotation exists

def test_emotion_detection_runs_before_and_independently_of_situation():
    interpretation = interpret_query("I miss someone who is far away, and I keep waiting for them.", load_corpus())
    assert interpretation["processing_order"][:3] == ["emotion detection", "situation understanding", "contextual interpretation"]
    assert interpretation["emotion_detection"]["primary"] == "longing"
    assert interpretation["emotion"]["value"] == "longing"
    assert interpretation["situation"]["value"] == "waiting for a loved one's return"

def test_emotion_detection_handles_core_examples_and_ambiguity():
    assert detect_rule_based_emotions("I am so happy that we are reunited.")["primary"] == "joy"
    assert detect_rule_based_emotions("I am angry about the conflict in my relationship.")["primary"] == "anger"
    assert detect_rule_based_emotions("I am afraid that our journey will separate us.")["primary"] == "fear"
    neutral = detect_rule_based_emotions("The road is quiet this morning.")
    assert neutral["primary"] == "" and neutral["confidence"] == "uncertain"

def test_generic_love_alone_does_not_dominate_keyword_ranking():
    rows = load_corpus()
    assert keyword_results(rows, "love") == []
    results, _ = retrieve(rows, "Emotion-aware", "I miss someone far away and keep waiting for return.")
    assert results and all(result["row"]["poem_id"].startswith("NT") for result in results)

def test_pretrained_output_format_and_explicit_fallback_without_download():
    formatted = format_pretrained_output([[{"label":"sadness","score":0.7},{"label":"joy","score":0.2},{"label":"neutral","score":0.1}]])
    assert formatted["primary"] == "sadness"
    assert formatted["confidence"] == 0.7
    assert formatted["model_name"] == MODEL_NAME
    fallback = detect_emotions("I miss someone far away and keep waiting.")
    assert "fallback" in fallback["method"] and fallback["fallback_reason"]

def _mocked_pretrained(label, confidence):
    return {
        "method": "pretrained Hugging Face Transformers model",
        "model_name": MODEL_NAME,
        "primary": label,
        "secondary": [],
        "confidence": confidence,
        "confidence_label": "model probability score",
        "alternative_scores": {label: confidence},
        "evidence": {},
        "fallback_reason": "",
    }

@pytest.mark.parametrize(("query", "label", "confidence", "contextual", "situation"), [
    ("I'm waiting for someone I love to return.", "joy", .7547, "longing", "waiting for a loved one's return"),
    ("I felt joyful when I finally met the person I had missed.", "joy", .9928, "", "reunion after separation"),
    ("I am angry because someone I love has misunderstood me.", "anger", .9910, "relationship distress", "relationship conflict"),
    ("I'm afraid my journey will separate me from someone I love.", "fear", .9921, "", "fear of separation during a journey"),
    ("I don't know what I feel about this situation.", "disgust", .6977, "uncertainty", ""),
])
def test_actual_model_outputs_are_preserved_while_context_is_sentence_based(monkeypatch, query, label, confidence, contextual, situation):
    monkeypatch.setattr("src.retrieval.core.detect_emotions", lambda _: _mocked_pretrained(label, confidence))
    interpretation = interpret_query(query, load_corpus())
    model = interpretation["emotion_detection"]
    assert model["primary"] == label
    assert model["confidence"] == confidence
    assert model["model_name"] == MODEL_NAME
    assert interpretation["contextual_interpretation"]["value"] == contextual
    assert interpretation["situation"]["value"] == situation

def test_contextual_interpretation_uses_explicit_cues_only():
    assert contextual_interpretation("I cannot wait for my loved one to arrive.")["value"] == "anticipation"
    assert contextual_interpretation("The road is quiet this morning.")["value"] == ""

def test_api_returns_emotion_model_metadata_without_network():
    response = search(RetrieveRequest(query="I am angry because someone I love has misunderstood me."))
    emotion = response["interpretation"]["emotion_detection"]
    assert emotion["model_name"] == MODEL_NAME
    assert "method" in emotion and "alternative_scores" in emotion
    assert response["results"] and response["results"][0]["poem_id"].startswith(("NT", "TK"))

def test_single_situation_guard_and_explicit_context_detection():
    interpretation = interpret_query("I wait for them. I meet them at night.", load_corpus())
    assert interpretation["situation"]["value"] == "secret meeting at night"
    query = "I am worried that my journey will separate me from someone I love."
    interpretation = interpret_query(query, load_corpus())
    assert interpretation["situation"]["value"] == "fear of separation during a journey"
    assert interpretation["relationship"]["value"] == "lovers / intimate relationship"
    assert interpretation["domain"]["value"] == "Akam"
    assert interpretation["tinai"]["value"] == ""

def test_vector_evidence_excludes_generic_character_roles():
    results = vector_results(load_corpus(), "I want to meet my loved one secretly at night.")
    assert results and "friend" not in str(results[0]["evidence"])
    assert "friend" not in results[0]["explanation"]

def test_tfidf_real_annotation_overlap_is_nonzero():
    results = vector_results(load_corpus(), "I want to meet my loved one secretly at night.")
    assert results[0]["score"] > 0
    assert "meeting" in results[0]["evidence"].get("situation", []) or "meeting" in results[0]["evidence"].get("keywords", []) or "meeting" in results[0]["evidence"].get("chapter_gloss_en", [])

def test_api_rejects_multiple_contexts():
    with pytest.raises(HTTPException) as error:
        search(RetrieveRequest(query="I wait for them. I meet them at night. I travel tomorrow."))
    assert error.value.status_code == 422

def test_frontend_has_one_default_query_and_replaces_it_with_an_example():
    source = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert 'const defaultQuery = "I\'m waiting for someone I love to return."' in source
    assert "onClick={()=>setQuery(example)}" in source
    assert "api.retrieve({query:query.trim(),model,emotion})" in source

@pytest.mark.parametrize(("model", "query"), [
    ("Keyword matching", "I want to meet my loved one secretly at night."),
    ("Vector similarity fallback", "I want to meet my loved one secretly at night."),
    ("Emotion-aware", "My relationship is troubled by conflict."),
    ("Culturally grounded routing", "I'm worried that my journey will separate me from someone I love."),
])
def test_retrieval_methods_return_only_positive_scores_with_evidence(model, query):
    results, _ = retrieve(load_corpus(), model, query)
    assert results
    assert all(result["score"] > 0 and result["evidence"] for result in results)

@pytest.mark.parametrize("model", ["Keyword matching", "Vector similarity fallback", "Emotion-aware", "Culturally grounded routing"])
def test_zero_score_candidates_are_not_presented_as_results(model):
    results, context = retrieve(load_corpus(), model, "Xylophones resonate beneath a satellite.")
    assert results == []
    assert any("No strong corpus match" in message for message in context)

def test_api_no_match_response_does_not_serialize_arbitrary_first_records():
    response = search(RetrieveRequest(query="Xylophones resonate beneath a satellite."))
    assert response["no_strong_match"] is True
    assert response["results"] == []
    assert any("No strong corpus match" in message for message in response["context"])

def test_semantic_retrieval_can_be_disabled_without_loading_weights():
    results, context = retrieve(load_corpus(), "Semantic retrieval", "An unfamiliar description of a quiet reunion.")
    assert results == []
    assert "Semantic retrieval unavailable" in context[0]

def test_semantic_model_is_explicitly_unavailable_when_disabled(monkeypatch):
    monkeypatch.setenv(DISABLE_ENV, "1")
    get_semantic_model.cache_clear()
    with pytest.raises(SemanticModelUnavailable, match=DISABLE_ENV):
        get_semantic_model()
    get_semantic_model.cache_clear()

def test_hybrid_combines_semantic_and_tfidf_components(monkeypatch):
    row = {"collection": "Natrinai", "poem_id": "NT001", "poem_number": "1"}
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([{"row": row, "score": .8, "evidence": {"semantic": ["similarity"]}, "explanation": "semantic"}], ""))
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [{"row": row, "score": .5, "evidence": {"keywords": ["waiting"]}, "explanation": "tfidf"}])
    results, unavailable = hybrid_results([row], "waiting")
    assert not unavailable and results[0]["score"] == 1.0
    assert results[0]["evidence"] == {"keywords": ["waiting"], "semantic": ["similarity"]}
    assert "semantic (70%) and TF-IDF (30%)" in results[0]["score_type"]

@pytest.mark.skipif(os.getenv("CLASSICAL_TAMIL_RUN_SEMANTIC_INTEGRATION") != "1", reason="set CLASSICAL_TAMIL_RUN_SEMANTIC_INTEGRATION=1 to use an already cached local model")
def test_live_semantic_and_hybrid_with_cached_model(monkeypatch, tmp_path):
    """Opt-in only: never downloads weights and writes any temporary vectors outside the repo."""
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    monkeypatch.delenv(ALLOW_DOWNLOAD_ENV, raising=False)
    monkeypatch.setenv(CACHE_ENV, str(tmp_path))
    get_semantic_model.cache_clear()
    rows = [row for row in load_corpus() if row["collection"] == "Natrinai"][:2]
    semantic, unavailable = semantic_results(rows, "waiting for a return")
    if unavailable:
        pytest.skip(f"local semantic model unavailable: {unavailable}")
    hybrid, hybrid_unavailable = hybrid_results(rows, "waiting for a return")
    assert semantic and not hybrid_unavailable and hybrid
    assert "Cross-lingual embedding" in semantic[0]["score_type"]
    assert "semantic (70%) and TF-IDF (30%)" in hybrid[0]["score_type"]
    get_semantic_model.cache_clear()

def test_semantic_result_format_is_truthful_when_encoder_is_mocked(monkeypatch):
    rows = load_corpus()[:2]
    monkeypatch.setattr("src.retrieval.core.corpus_embeddings", lambda documents: __import__("numpy").array([[1.0, 0.0], [0.0, 1.0]]))
    monkeypatch.setattr("src.retrieval.core.encode", lambda texts, prefix: __import__("numpy").array([[1.0, 0.0]]))
    results, unavailable = semantic_results(rows, "A previously unseen English situation")
    assert not unavailable and results[0]["row"]["poem_id"] == rows[0]["poem_id"]
    assert results[0]["score"] == 1.0
    assert "semantic" in results[0]["evidence"]

def test_semantic_dispatch_accepts_space_less_method_name(monkeypatch):
    rows = load_corpus()[:2]
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda rows, query: ([{"row": rows[0], "score": .8, "evidence": {"semantic": ["mocked"]}, "explanation": "mocked"}], ""))
    results, context = retrieve(rows, "Semanticretrieval", "A new sentence.")
    assert results[0]["row"]["poem_id"] == rows[0]["poem_id"]
    assert "semantic retrieval" in context[0].casefold()

@pytest.mark.parametrize(("ui_model", "retrieval_model"), [
    ("Semantic Retrieval", "Semantic retrieval"),
    ("Hybrid Retrieval", "Hybrid retrieval"),
    ("Auto (rank fusion)", "auto"),
])
def test_api_dispatches_semantic_and_auto_methods_from_the_ui(monkeypatch, ui_model, retrieval_model):
    captured = {}
    monkeypatch.setattr("api.retrieve", lambda rows, model, *args: (captured.setdefault("model", model) and [], []))
    search(RetrieveRequest(query="I am waiting for someone I love to return.", model=ui_model))
    assert captured["model"] == retrieval_model

def test_friendship_is_not_interpreted_as_romantic():
    interpretation = interpret_query("I miss my old friend.", load_corpus())
    assert interpretation["contextual_interpretation"]["value"] == "longing"
    assert interpretation["relationship"]["value"] == "friendship"
    assert interpretation["domain"]["value"] == ""
    assert interpretation["tinai"]["value"] == "" and interpretation["uri"]["value"] == ""

def test_api_rejects_whitespace_only_query_with_clear_message():
    with pytest.raises(HTTPException, match="Enter a sentence"):
        search(RetrieveRequest(query="   "))

def test_semantic_encoder_uses_e5_passage_prefix(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv("CLASSICAL_TAMIL_EMBEDDING_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr("src.retrieval.semantic_model.encode", lambda texts, prefix: calls.append((texts, prefix)) or __import__("numpy").array([[1.0, 0.0]]))
    corpus_embeddings(["a poem"])
    assert calls == [(["a poem"], "passage: ")]

def test_semantic_weak_match_uses_configured_spread(monkeypatch):
    monkeypatch.setattr("src.retrieval.core.SEMANTIC_WEAK_SPREAD", .03)
    items = [{"score": .80, "evidence": {"semantic": ["similarity"]}}, {"score": .79, "evidence": {"semantic": ["similarity"]}}]
    assert all(item["weak_match"] for item in _mark_semantic_weak_matches(items))

def test_auto_rank_fusion_returns_unique_rows_with_rank_evidence(monkeypatch):
    rows = [{"collection": "Natrinai", "poem_id": "NT001", "poem_number": "1"}, {"collection": "Thirukkural", "poem_id": "TK0001", "poem_number": "1"}]
    def item(row, score=1.0): return {"row": row, "score": score, "evidence": {"mock": ["evidence"]}, "explanation": "mock"}
    monkeypatch.setattr("src.retrieval.core.keyword_results", lambda *_: [item(rows[0]), item(rows[1])])
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [item(rows[1]), item(rows[0])])
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([item(rows[0])], ""))
    results, methods, unavailable = auto_results(rows, "query")
    assert methods == ["keyword", "tfidf", "semantic"]
    assert unavailable == []
    assert len(results) == 2 and len({(x["row"]["collection"], x["row"]["poem_id"]) for x in results}) == 2
    assert results[0]["score_type"] == "Reciprocal rank fusion score; not a probability"
    assert "Rank fusion:" in results[0]["explanation"]

def test_auto_abstains_when_every_component_abstains(monkeypatch):
    monkeypatch.setattr("src.retrieval.core.keyword_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([], ""))
    monkeypatch.setattr("src.retrieval.core.hybrid_results", lambda *_: ([], ""))
    results, context = retrieve([], "auto", "xylophones beneath a satellite")
    assert results == [] and any("No strong corpus match" in message for message in context)


def test_auto_abstains_for_weak_semantic_only_neighbours(monkeypatch):
    row = {"collection": "Thirukkural", "poem_id": "TK0001", "poem_number": "1"}
    item = {"row": row, "score": .22, "evidence": {"semantic": ["cross-lingual similarity"]}, "explanation": "semantic", "weak_match": True}
    monkeypatch.setattr("src.retrieval.core.keyword_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([item], ""))
    results, context = retrieve([row], "auto", "Xylophones resonate beneath a satellite.")
    assert results == [] and any("No strong corpus match" in message for message in context)


def test_auto_keeps_nonweak_semantic_result_for_differently_worded_query(monkeypatch):
    row = {"collection": "Natrinai", "poem_id": "NT001", "poem_number": "1"}
    item = {"row": row, "score": .72, "evidence": {"semantic": ["cross-lingual similarity"]}, "explanation": "semantic", "weak_match": False}
    monkeypatch.setattr("src.retrieval.core.keyword_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [])
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([item], ""))
    monkeypatch.setattr("src.retrieval.core._mark_semantic_weak_matches", lambda items: items)
    results, _ = retrieve([row], "auto", "I ache for a distant person.")
    assert results and results[0]["row"]["poem_id"] == "NT001"


@pytest.mark.parametrize(("query", "situation", "relationship"), [
    ("I miss my old friend and wish we could reconnect.", "missing an old friend and wanting to reconnect", "friendship"),
    ("I feel lonely even when surrounded by people.", "loneliness despite being around people", ""),
    ("I am worried about my future.", "worry about the future", ""),
    ("I feel left behind while everyone else moves forward.", "feeling left behind while others move forward", ""),
    ("My friend and I are having an argument.", "friendship difficulty", "friendship"),
    ("I am uncertain about a difficult decision.", "personal uncertainty about a difficult decision", ""),
])
def test_additional_human_situations_are_conservative(query, situation, relationship):
    interpretation = interpret_query(query, load_corpus())
    assert interpretation["situation"]["value"] == situation
    assert interpretation["relationship"]["value"] == relationship
    assert interpretation["tinai"]["value"] == ""

def test_auto_does_not_change_direct_method_results():
    rows = load_corpus()
    before = retrieve(rows, "Vector similarity fallback", "anger")
    retrieve(rows, "auto", "anger")
    after = retrieve(rows, "Vector similarity fallback", "anger")
    assert before == after

def test_thirukkural_parser_excludes_colophons_and_keeps_kural_1330_intact():
    from scripts.build_combined_corpus import RAW_PATH, parse_thirukkural
    rows = parse_thirukkural(RAW_PATH.read_text(encoding="utf-8"))
    assert len(rows) == 1330
    assert all("முற்றிற்று" not in row["poem_text"] and "this page was first put up" not in row["poem_text"].casefold() for row in rows)
    assert len(rows[-1]["poem_text"].splitlines()) == 2

def test_business_partner_is_not_interpreted_as_lovers():
    interpretation = interpret_query("My business partner and I run a shop.", load_corpus())
    assert interpretation["relationship"]["value"] == "colleague / associate"
    assert interpretation["domain"]["value"] == ""

def test_auto_reports_unavailable_semantic_component(monkeypatch):
    row = {"collection": "Natrinai", "poem_id": "NT001", "poem_number": "1"}
    item = {"row": row, "score": 1.0, "evidence": {"keyword": ["match"]}, "explanation": "match"}
    monkeypatch.setattr("src.retrieval.core.keyword_results", lambda *_: [item])
    monkeypatch.setattr("src.retrieval.core.vector_results", lambda *_: [item])
    monkeypatch.setattr("src.retrieval.core.semantic_results", lambda *_: ([], "unavailable"))
    results, context = retrieve([row], "auto", "query")
    assert results and any("Semantic unavailable" in message and "Used methods: keyword, tfidf." in message for message in context)

def test_optional_meanings_loader_handles_new_columns_and_missing_ids(tmp_path):
    absent = tmp_path / "absent.csv"
    assert load_meanings(absent) == {}
    meanings = tmp_path / "meanings_en.csv"
    meanings.write_text("\ufeffcollection,id,plain_meaning,speaker_context,real_life_example,meaning_source\n thIRUkKuRaL , 56 ,A paraphrase,A speaker,A modern example,editorial\n", encoding="utf-8")
    rows = load_corpus(meanings_path=meanings)
    found = next(row for row in rows if row["poem_id"] == "TK0056")
    assert found["plain_meaning"] == found["meaning_en"] == "A paraphrase"
    assert found["speaker_context"] == "A speaker"
    assert next(row for row in rows if row["poem_id"] == "TK0057")["plain_meaning"] == ""


def test_optional_meanings_loader_accepts_legacy_and_header_only_files(tmp_path):
    legacy = tmp_path / "legacy.csv"
    legacy.write_text("collection,id,meaning_en,meaning_source\nNatrinai,1,Legacy meaning,editorial\n", encoding="utf-8")
    assert load_meanings(legacy)[("natrinai", "nt001")]["plain_meaning"] == "Legacy meaning"
    header_only = tmp_path / "header_only.csv"
    header_only.write_text("collection,id,plain_meaning,speaker_context,real_life_example,meaning_source\n", encoding="utf-8")
    assert load_meanings(header_only) == {}


def test_meaning_source_is_preserved_without_branding_rewrite(tmp_path):
    meanings = tmp_path / "meanings_en.csv"
    meanings.write_text('collection,id,meaning_en,meaning_source\nNatrinai,1,Meaning,Unverified explanation\n', encoding="utf-8")
    assert load_meanings(meanings)[("natrinai", "nt001")]["meaning_source"] == "Unverified explanation"


def test_optional_curated_meanings_are_safe_and_secondary_to_meanings_file(tmp_path):
    absent = tmp_path / "absent_curated.csv"
    assert load_curated_meanings(absent) == {}
    curated = tmp_path / "natrinai_curated.csv"
    curated.write_text("\ufeffcollection,id,plain_meaning,speaker_context,real_life_example,meaning_source,situation,emotion,modern_theme,confidence,review_status,notes\nNatrinai,1,Curated meaning,Speaker,,curated source,situation,emotion,theme,low,draft,note\n", encoding="utf-8")
    meanings = tmp_path / "meanings_en.csv"
    meanings.write_text("collection,id,plain_meaning,speaker_context,real_life_example,meaning_source\nNatrinai,1,Preferred meaning,,,meanings source\n", encoding="utf-8")
    preferred = next(row for row in load_corpus(meanings_path=meanings, curated_path=curated) if row["poem_id"] == "NT001")
    assert preferred["plain_meaning"] == "Preferred meaning"
    assert preferred["confidence"] == "medium"
    assert next(row for row in load_corpus(meanings_path=meanings, curated_path=curated) if row["poem_id"] == "NT002")["plain_meaning"] == ""
    low_confidence = next(row for row in load_corpus(meanings_path=tmp_path / "missing_meanings.csv", curated_path=curated) if row["poem_id"] == "NT001")
    assert low_confidence["confidence"] == "low"


def test_default_curated_meanings_source_is_the_corrected_file():
    from src.retrieval.core import CURATED_PATH
    assert CURATED_PATH.name == "Natrinai_399_meanings_fixed.csv"
    assert len(load_curated_meanings()) == 399


def test_api_serializes_display_only_curated_fields():
    row = {**MEANING_DEFAULTS, "plain_meaning": "Meaning", "confidence": "high", "review_status": "reviewed"}
    item = {"row": row, "score": 1.0, "score_type": "test", "explanation": "test", "evidence": []}
    response = serialize(item, 1)
    assert response["plain_meaning"] == "Meaning"
    assert response["confidence"] == "high"
    assert response["review_status"] == "reviewed"
