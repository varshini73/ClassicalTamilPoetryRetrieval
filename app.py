from __future__ import annotations

import csv
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.retrieval.core import TINAI, URI, corpus_statistics, load_corpus, retrieve

st.set_page_config(page_title="Classical Tamil Poetry Retrieval", layout="wide")

@st.cache_data
def corpus():
    return load_corpus()

@st.cache_data
def evaluation_rows():
    with (ROOT / "data" / "evaluation" / "modern_query_pilot.csv").open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))

rows = corpus()
st.title("Culturally Grounded Retrieval of Classical Tamil Poetry")
st.caption("Pilot: retrieves existing Natrinai records; it does not generate poems or translations.")
retrieval, evaluation, data = st.tabs(["Poetry retrieval", "Pilot evaluation", "Dataset"])

with retrieval:
    query = st.text_area("Modern emotional situation", value="I love someone, but we are separated. I keep thinking about them and waiting for them to come back.", height=90)
    model = st.selectbox("Retrieval model", ["Keyword matching", "Vector similarity fallback", "Emotion-aware", "Culturally grounded routing"])
    c1, c2, c3 = st.columns(3)
    with c1:
        emotion = st.selectbox("Optional emotion context", [""] + sorted({r["emotion"] for r in rows if r["emotion"]}), format_func=lambda x: x or "No selection")
    with c2:
        tinai = st.selectbox("Optional Tinai constraint (user-supplied)", [""] + list(TINAI), format_func=lambda x: x or "No selection")
    with c3:
        uri = st.selectbox("Optional Uri constraint (user-supplied)", [""] + list(URI), format_func=lambda x: x or "No selection")
    if st.button("Retrieve poems", type="primary"):
        results, context = retrieve(rows, model, query, emotion, tinai, uri)
        st.info(" ".join(context))
        for rank, item in enumerate(results, 1):
            row = item["row"]
            with st.expander(f"{rank}. Natrinai {row['poem_number']} — score {item['score']:.3f}", expanded=rank <= 3):
                st.write(row["poem_text"])
                st.caption(item["explanation"])
                st.write({"Tinai": row["tinai"] or "not annotated", "Uri": row["uri"] or "unresolved", "Emotion": row["emotion"] or "not annotated", "Situation": row["situation"] or "not annotated", "Characters": row["characters"] or "not annotated", "Keywords": row["keywords"] or "not annotated", "Status": row["annotation_status"]})
                st.markdown(f"Source: [{row['source']}]({row['source_url']})")

with evaluation:
    st.subheader("Modern-situation pilot set")
    st.write("Six actual-corpus query candidates are marked  . Candidate IDs are review prompts, not gold judgments; definitive P@K, R@K, and MRR are withheld.")
    st.dataframe(evaluation_rows(), use_container_width=True, hide_index=True)
    st.info("Metric status: 0 eligible queries with reviewed relevance judgments. Metric code is unit-tested with explicit synthetic judgments.")

with data:
    stats = corpus_statistics(rows)
    st.metric("Usable Natrinai records", stats["records"])
    st.write({"Emotion populated":stats["emotion"], "Situation populated":stats["situation"], "Characters populated":stats["characters"], "Keywords populated":stats["keywords"], "Uri populated":stats["uri"]})
    st.caption("Poem 234 is excluded. Poem 385 is retained as source-incomplete. Blank fields and needs_review are uncertainty, not negative evidence.")
