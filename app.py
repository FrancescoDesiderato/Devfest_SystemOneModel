import hashlib
import json
import re
import threading
import time
from pathlib import Path

import graphviz
import streamlit as st

from llm_planner_local import load_router, route_request, llm_plan

st.set_page_config(page_title="Mission Control", page_icon="🧭", layout="wide")

@st.cache_resource
def router_resource():
    return load_router(), threading.Lock()

def workflow(routes, route=None, score=None, fallback=None, phase="idle"):
    g = graphviz.Digraph()
    g.attr(rankdir="LR", bgcolor="transparent")
    g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fillcolor="#eef2f7")
    g.node("input", "Richiesta")
    label = "GLiNER multilingue\nCPU"
    if score is not None:
        label += f"\n{route} | score {score:.3f}"
    g.node("router", label, fillcolor="#bfdbfe")
    g.node("gate", "Gate / soglia", shape="diamond")
    g.node("llm", "Gemma 3 4B\nOllama planner", fillcolor="#ddd6fe" if fallback else "#eef2f7")
    g.edge("input", "router")
    g.edge("router", "gate")
    for i, r in enumerate(routes):
        active = phase == "done" and fallback is False and r["id"] == route
        g.node(f"route_{i}", r["id"], fillcolor="#bbf7d0" if active else "#eef2f7")
        g.edge("gate", f"route_{i}", color="#16a34a" if active else "#cbd5e1", penwidth="3" if active else "1")
    g.edge("gate", "llm", label="Score basso / override", color="#7c3aed" if fallback else "#cbd5e1", penwidth="3" if fallback else "1")
    g.node("plan", "Piano strutturato\n(non eseguito)", fillcolor="#ddd6fe" if fallback else "#eef2f7")
    g.edge("llm", "plan", color="#7c3aed" if fallback else "#cbd5e1")
    return g

def plan_graph(plan):
    g = graphviz.Digraph()
    g.attr(rankdir="LR")
    g.attr("node", shape="box", style="rounded,filled", fillcolor="#ede9fe", fontname="Helvetica")
    ids = {s["id"]: f"step_{i}" for i, s in enumerate(plan["steps"])}
    for s in plan["steps"]:
        label = f"{s['id']} · {s['tool']}\n{s['task']}\nCondizione: {s['run_if']}"
        g.node(ids[s["id"]], label=label)
        for dep in s["depends_on"]:
            g.edge(ids[dep], ids[s["id"]])
    return g

st.title("🧭 Mission Control")
st.caption("Decision model → gate → percorso diretto oppure LLM planner. Gli strumenti non vengono eseguiti.")

with st.sidebar:
    st.header("Dati e configurazione")
    source = st.radio("Sorgente", ["File locali", "Carica file"])
    if source == "File locali":
        folder = st.text_input("Cartella dei dati", str(Path(__file__).resolve().parent / "llm_planner"))
        root = Path(folder).expanduser()
        jsons = sorted(root.glob("*.json")) if root.is_dir() else []
        txts = sorted(root.glob("*.txt")) if root.is_dir() else []
        if not jsons or not txts:
            st.info("Indica una cartella contenente almeno un JSON e un TXT oppure usa Carica file.")
            st.stop()
        route_path = st.selectbox("File delle route", jsons, format_func=lambda p:p.name)
        text_path = st.selectbox("File dei casi", txts, format_func=lambda p:p.name)
        route_bytes, text_bytes = route_path.read_bytes(), text_path.read_bytes()
    else:
        route_file = st.file_uploader("Route JSON", type=["json"])
        text_file = st.file_uploader("Casi TXT", type=["txt"])
        if route_file is None or text_file is None:
            st.info("Carica entrambi i file.")
            st.stop()
        route_bytes, text_bytes = route_file.getvalue(), text_file.getvalue()
    threshold = st.slider("Soglia di escalation", 0.0, 1.0, 0.8, 0.01)
    force = st.checkbox("Forza LLM — override manuale")
    st.caption("Lo score non è una probabilità calibrata. Il caso difficile può avere score alto.")

try:
    routes = json.loads(route_bytes.decode("utf-8-sig"))["routes"]
    if not isinstance(routes, list) or not routes or any(
        not isinstance(r, dict) or not isinstance(r.get("id"), str) or not r["id"].strip()
        or not isinstance(r.get("description"), str) for r in routes
    ) or len({r["id"] for r in routes}) != len(routes):
        raise ValueError("Route vuote, duplicate o non valide.")
    texts = [s.strip() for s in re.split(r"=== TESTO \d+ ===", text_bytes.decode("utf-8-sig")) if s.strip()]
    if not texts:
        raise ValueError("Nessun testo disponibile.")
except Exception as exc:
    st.error(f"File non validi: {exc}")
    st.stop()

fingerprint = hashlib.sha256(route_bytes + text_bytes).hexdigest()
left, right = st.columns([1, 1.4])
with left:
    st.subheader("Richiesta")
    index = st.selectbox("Scegli un caso", range(len(texts)), format_func=lambda i: f"Testo {i+1}: {texts[i][:65]}…", key=f"case_{fingerprint}")
    text = st.text_area("Testo modificabile", texts[index], height=240, key=f"text_{fingerprint}_{index}")
    run = st.button("Esegui routing e piano", type="primary", disabled=not text.strip())
    with st.expander("Route disponibili"):
        st.dataframe(routes, use_container_width=True, hide_index=True)
with right:
    st.subheader("Percorso decisionale")
    graph_slot = st.empty()

signature = hashlib.sha256(json.dumps([fingerprint, text, threshold, force], ensure_ascii=False).encode()).hexdigest()
record = st.session_state.get("mission_result")
if record and record["signature"] != signature:
    st.info("Input o configurazione modificati: esegui nuovamente per aggiornare il risultato.")
    record = None

graph_slot.graphviz_chart(workflow(routes))
if run:
    start = time.perf_counter()
    result = {"input":text, "threshold":threshold, "force_llm":force}
    try:
        with st.spinner("Caricamento router e classificazione su CPU…"):
            router, lock = router_resource()
            route_start = time.perf_counter()
            with lock:
                route, score = route_request(router, text, routes)
            result.update(route=route, score=score, router_ms=round((time.perf_counter()-route_start)*1000,1))
        fallback = force or score < threshold
        result.update(mode="llm_planner" if fallback else "direct", fallback_reason="manual_override" if force else ("below_threshold" if fallback else None))
        graph_slot.graphviz_chart(workflow(routes, route, score, fallback, "planning" if fallback else "done"))
        llm_start = time.perf_counter()
        if fallback:
            with st.spinner("Gemma sta costruendo il piano tramite Ollama…"):
                plan = llm_plan(text, routes)
        else:
            plan = {"steps":[{"id":"step_1", "tool":route, "task":text, "depends_on":[], "run_if":"always"}], "completion_condition":"Eseguire il percorso selezionato; nessuno strumento è stato eseguito."}
        result.update(plan=plan, planner_ms=round((time.perf_counter()-llm_start)*1000,1) if fallback else 0, status="ok")
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
    result["total_ms"] = round((time.perf_counter()-start)*1000,1)
    record = {"signature":signature, "result":result}
    st.session_state["mission_result"] = record

if record:
    result = record["result"]
    if "score" in result:
        fallback = result["mode"] == "llm_planner"
        graph_slot.graphviz_chart(workflow(routes, result["route"], result["score"], fallback, "done"))
        a,b,c,d = st.columns(4)
        a.metric("Route GLiNER", result["route"])
        b.metric("Score", f"{result['score']:.3f}")
        c.metric("Percorso", "LLM planner" if fallback else "Diretto")
        d.metric("Tempo totale", f"{result['total_ms']/1000:.2f} s")
        st.caption(f"Soglia: {result['threshold']:.2f} · Router: {result['router_ms']} ms · Planner: {result.get('planner_ms', '—')} ms · Motivo fallback: {result['fallback_reason'] or 'nessuno'}")
    if result["status"] == "error":
        st.error(result["error"])
    else:
        st.subheader("Piano finale — non eseguito")
        st.graphviz_chart(plan_graph(result["plan"]))
        st.dataframe(result["plan"]["steps"], use_container_width=True, hide_index=True)
        st.info(result["plan"]["completion_condition"])
    with st.expander("Output JSON", expanded=False):
        st.json(result)
    st.download_button("Esporta risultato JSON", json.dumps(result, ensure_ascii=False, indent=2), file_name="mission_control_result.json", mime="application/json")
