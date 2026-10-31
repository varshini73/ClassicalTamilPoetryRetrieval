"""FastAPI surface for the preserved Natrinai retrieval pilot."""
from __future__ import annotations

import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.retrieval.core import TINAI, URI, corpus_statistics, interpret_query, load_corpus, retrieve, submitted_sentences

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Classical Tamil Poetry Retrieval API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    model: str = "Auto (rank fusion)"
    emotion: str = ""
    tinai: str = ""
    uri: str = ""
    limit: int = Field(default=10, ge=1, le=30)

MODEL_MAP = {"Keyword Matching":"Keyword matching", "TF-IDF Retrieval":"Vector similarity fallback", "Emotion-Aware Retrieval":"Emotion-aware", "Culturally Grounded Tinai/Uri Routing":"Culturally grounded routing", "Semantic Retrieval":"Semantic retrieval", "Hybrid Retrieval":"Hybrid retrieval", "Auto (rank fusion)":"auto"}

def serialize(item: dict, rank: int) -> dict:
    row = item["row"]
    score = item["score"]
    relevance = "Weak match: limited corpus evidence; inspect the annotations and source." if item.get("weak_match") or (score < 0.10 and item.get("score_type") != "Reciprocal rank fusion score; not a probability") else "Ranked from available corpus annotations and retrieval evidence."
    return {"rank":rank, "score":score, "score_type":item.get("score_type", "TF-IDF cosine similarity / model-specific ranking score; not a probability"), "explanation":item["explanation"], "evidence":item["evidence"], "relevance_note":relevance, "weak_match":bool(item.get("weak_match")), **{key: row.get(key, "") for key in ("collection","poem_id","poem_number","title","section","chapter_gloss_en","meaning_en","plain_meaning","speaker_context","real_life_example","meaning_source","confidence","review_status","curated_situation","curated_emotion","modern_theme","curation_notes","poem_text","akam_puram","tinai","uri","emotion","situation","characters","keywords","source","source_url","annotation_notes","annotation_status")}}

@app.get("/api/health")
def health():
    return {"status":"ok", "service":"Classical Tamil Poetry Retrieval API"}

@app.get("/api/dataset/stats")
def stats():
    result = corpus_statistics(load_corpus())
    return {**result, "source":"Project Madurai Unicode Etexts PM296 (Natrinai) and PM001 (Thirukkural)", "notes":"Blank and needs_review annotations remain uncertainty; Tinai/Uri routing is limited to explicitly Akam records."}

@app.post("/api/retrieve")
def search(request: RetrieveRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Enter a sentence to search the corpus.")
    if request.model not in MODEL_MAP:
        raise HTTPException(status_code=422, detail="Unknown retrieval model.")
    if request.tinai and request.tinai not in TINAI:
        raise HTTPException(status_code=422, detail="Unknown Tinai constraint.")
    if request.uri and request.uri not in URI:
        raise HTTPException(status_code=422, detail="Unknown Uri constraint.")
    sentences = submitted_sentences(query)
    preset_examples = ("i'm waiting for someone i love to return", "i want to meet my loved one secretly at night", "my relationship is troubled by conflict", "i'm worried that my journey will separate me from someone i love")
    if len(sentences) > 2 or sum(example in query.casefold() for example in preset_examples) >= 2:
        raise HTTPException(status_code=422, detail="Please submit up to two sentences at a time; preset examples must be searched separately.")
    rows = load_corpus()
    results, context = retrieve(rows, MODEL_MAP[request.model], query, request.emotion, request.tinai, request.uri, request.limit)
    return {"model":request.model, "query":query, "interpretation":interpret_query(query, rows), "context":context, "no_strong_match":not results, "results":[serialize(item, i) for i, item in enumerate(results, 1)]}

@app.get("/api/evaluation/queries")
def evaluation_queries():
    path = ROOT / "data" / "evaluation" / "modern_query_pilot.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        queries = list(csv.DictReader(file))
    judgments_path = ROOT / "data" / "evaluation" / "human_relevance.csv"
    judgments = []
    if judgments_path.exists():
        with judgments_path.open(encoding="utf-8-sig", newline="") as file:
            judgments = [row for row in csv.DictReader(file) if (row.get("review_status") or "").strip().casefold() == "reviewed"]
    reviewed_queries = len({row.get("query_id") for row in judgments if row.get("query_id")})
    return {"queries":queries, "metrics_status":"ready_for_human_judgments" if not judgments else "reviewed_judgments_available", "reviewed_queries":reviewed_queries, "reviewed_judgments":len(judgments), "message":"P@K, R@K, MRR, and nDCG@K are unavailable until human relevance judgments are supplied; cultural evaluation applies only to Natrinai Akam records."}
