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
    query: str = Field(min_length=1, max_length=3000)
    model: str = "TF-IDF Retrieval"
    emotion: str = ""
    tinai: str = ""
    uri: str = ""
    limit: int = Field(default=10, ge=1, le=30)

MODEL_MAP = {"Keyword Matching":"Keyword matching", "TF-IDF Retrieval":"Vector similarity fallback", "Emotion-Aware Retrieval":"Emotion-aware", "Culturally Grounded Tinai/Uri Routing":"Culturally grounded routing"}

def serialize(item: dict, rank: int) -> dict:
    row = item["row"]
    score = item["score"]
    relevance = "Weak match: limited corpus evidence; inspect the annotations and source." if score < 0.10 else "Ranked from available corpus annotations and retrieval evidence."
    return {"rank":rank, "score":score, "score_type":"TF-IDF cosine similarity / model-specific ranking score; not a probability", "explanation":item["explanation"], "evidence":item["evidence"], "relevance_note":relevance, **{key: row.get(key, "") for key in ("poem_id","poem_number","poem_text","akam_puram","tinai","uri","emotion","situation","characters","keywords","source","source_url","annotation_notes","annotation_status")}}

@app.get("/api/health")
def health():
    return {"status":"ok", "service":"Classical Tamil Poetry Retrieval API"}

@app.get("/api/dataset/stats")
def stats():
    result = corpus_statistics(load_corpus())
    return {**result, "source":"Project Madurai Unicode Etext PM296", "notes":"Poem 234 is excluded; poem 385 is source-incomplete. Blank and needs_review annotations remain uncertainty."}

@app.post("/api/retrieve")
def search(request: RetrieveRequest):
    if request.model not in MODEL_MAP:
        raise HTTPException(status_code=422, detail="Unknown retrieval model.")
    if request.tinai and request.tinai not in TINAI:
        raise HTTPException(status_code=422, detail="Unknown Tinai constraint.")
    if request.uri and request.uri not in URI:
        raise HTTPException(status_code=422, detail="Unknown Uri constraint.")
    if len(submitted_sentences(request.query)) != 1:
        raise HTTPException(status_code=422, detail="Please submit one situation at a time. Multiple sentences can describe different contexts.")
    rows = load_corpus()
    results, context = retrieve(rows, MODEL_MAP[request.model], request.query, request.emotion, request.tinai, request.uri, request.limit)
    return {"model":request.model, "query":request.query, "interpretation":interpret_query(request.query, rows), "context":context, "no_strong_match":not results, "results":[serialize(item, i) for i, item in enumerate(results, 1)]}

@app.get("/api/evaluation/queries")
def evaluation_queries():
    path = ROOT / "data" / "evaluation" / "modern_query_pilot.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        queries = list(csv.DictReader(file))
    return {"queries":queries, "metrics_status":"pending_human_relevance_review", "message":"All pilot queries are unreviewed; P@K, R@K and MRR are not reported as definitive."}
