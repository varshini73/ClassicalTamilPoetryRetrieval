import os
from pathlib import Path
import pytest

os.environ["CLASSICAL_TAMIL_EMOTION_FORCE_FALLBACK"] = "1"

from fastapi import HTTPException
from api import RetrieveRequest, search
from src.retrieval.core import contextual_interpretation, cultural_results, detect_emotions, detect_rule_based_emotions, interpret_query, keyword_results, load_corpus, metrics, retrieve, vector_results
from src.retrieval.emotion_model import MODEL_NAME, format_pretrained_output

def test_corpus_loads():
    rows = load_corpus()
    assert len(rows) == 399
    assert all(r["poem_text"] and r["source_url"] for r in rows)
    assert not any(r["poem_number"] == "234" for r in rows)

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
    assert response["results"] and response["results"][0]["poem_id"].startswith("NT")

def test_single_situation_guard_and_explicit_context_detection():
    with pytest.raises(ValueError, match="one situation"):
        interpret_query("I wait for them. I meet them at night.", load_corpus())
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
    assert "meeting" in results[0]["evidence"].get("situation", []) or "meeting" in results[0]["evidence"].get("keywords", [])

def test_api_rejects_multiple_contexts():
    with pytest.raises(HTTPException) as error:
        search(RetrieveRequest(query="I wait for them. I meet them at night."))
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
