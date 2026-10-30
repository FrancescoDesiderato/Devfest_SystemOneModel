import json, re, time
from pathlib import Path
import requests
from gliner2 import AutoExtractor

MODEL_ID = "fastino/GLiNER2.5-multi-Decide"
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_URL = "http://127.0.0.1:11434"

def load_inputs(directory="."):
    directory = Path(directory)
    routes = json.loads((directory / "llm_planner/routes.json").read_text(encoding="utf-8"))["routes"]
    if not routes or len({r["id"] for r in routes}) != len(routes):
        raise ValueError("Route vuote o duplicate")
    raw = (directory / "llm_planner/cases.txt").read_text(encoding="utf-8")
    texts = [s.strip() for s in re.split(r"=== TESTO \d+ ===", raw) if s.strip()]
    return routes, texts

def load_router():
    router = AutoExtractor.from_pretrained(MODEL_ID)
    router.to("cpu")
    router.eval()
    return router

def route_request(router, text, routes):
    labels = {r["id"]: r["description"] for r in routes}
    schema = router.create_schema().classification("route", labels)
    result = router.extract(text, schema, include_confidence=True)
    prediction = result["route"]
    if not isinstance(prediction, dict) or "confidence" not in prediction:
        raise RuntimeError(f"Score non disponibile: {result}. Controllare la versione di gliner2.")
    score = float(prediction["confidence"])
    if not 0 <= score <= 1:
        raise ValueError(f"Score inatteso: {score}")
    if prediction["label"] not in labels:
        raise ValueError(f"Route inattesa: {prediction}")
    return prediction["label"], score

def validate_plan(plan, routes):
    allowed = {r["id"] for r in routes}
    if not isinstance(plan, dict) or not isinstance(plan.get("steps"), list) or not plan["steps"]:
        raise ValueError("Piano senza passaggi")
    seen = set()
    for step in plan["steps"]:
        if not isinstance(step, dict):
            raise ValueError("Passaggio non valido")
        sid = step.get("id")
        if not isinstance(sid, str) or not sid or sid in seen:
            raise ValueError("ID mancante o duplicato")
        if step.get("tool") not in allowed:
            raise ValueError("Strumento non consentito")
        deps = step.get("depends_on")
        if not isinstance(deps, list) or any(not isinstance(d, str) or d not in seen for d in deps):
            raise ValueError("Dipendenza mancante, futura o ciclica")
        for field in ("task", "run_if"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                raise ValueError(f"Campo mancante: {field}")
        seen.add(sid)
    if not isinstance(plan.get("completion_condition"), str):
        raise ValueError("completion_condition mancante")
    return plan

def llm_plan(text, routes):
    allowed_tools = [route["id"] for route in routes]

    plan_schema = {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "tool": {
                            "type": "string",
                            "enum": allowed_tools,
                        },
                        "task": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "run_if": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "required": [
                        "id",
                        "tool",
                        "task",
                        "depends_on",
                        "run_if",
                    ],
                    "additionalProperties": False,
                },
            },
            "completion_condition": {
                "type": "string",
                "minLength": 1,
            },
        },
        "required": ["steps", "completion_condition"],
        "additionalProperties": False,
    }

    system_prompt = """
Sei un planner. Trasforma la richiesta in un piano operativo.

Regole:
- Non eseguire gli strumenti: produci soltanto il piano.
- Non inventare risultati, tassi di cambio, policy o dati mancanti.
- Non effettuare prenotazioni.
- Usa soltanto gli strumenti disponibili.
- Ogni passaggio deve avere un identificatore univoco.
- Le dipendenze devono riferirsi soltanto a passaggi precedenti.
- Usa "always" per i passaggi senza condizioni.
- Per i passaggi condizionali, indica una condizione esplicita.
- Non chiedere subito dati recuperabili dagli strumenti.
- Se la policy risultasse incompleta, prevedi un chiarimento.
- Includi sempre completion_condition: descrive quando il piano
  dispone delle informazioni necessarie per fornire il risultato finale.
- Restituisci soltanto JSON conforme allo schema.
"""

    system_prompt += (
        "\nSTRUMENTI DISPONIBILI:\n"
        + json.dumps(routes, ensure_ascii=False)
        + "\nSCHEMA DELL'OUTPUT:\n"
        + json.dumps(plan_schema, ensure_ascii=False)
    )

    response = requests.post(
        OLLAMA_URL + "/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            # Passa lo schema, non soltanto la stringa "json".
            "format": plan_schema,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 1800,
                "num_ctx": 4096,
            },
        },
        timeout=300,
    )
    response.raise_for_status()

    data = response.json()
    raw_output = data["message"]["content"]

    try:
        plan = json.loads(raw_output)
        return validate_plan(plan, routes)

    except (ValueError, TypeError, KeyError) as exc:
        raise RuntimeError(
            "Il planner ha restituito un piano non valido.\n"
            f"Motivo: {exc}\n"
            f"Fine generazione: {data.get('done_reason', 'non disponibile')}\n"
            f"Output originale:\n{raw_output}"
        ) from exc

def run_demo(router, text, routes, threshold=0.8, force_llm=False):
    start = time.perf_counter()
    route, score = route_request(router, text, routes)
    router_ms = (time.perf_counter() - start) * 1000
    fallback = force_llm or score < threshold
    if fallback:
        plan = llm_plan(text, routes)
    else:
        plan = {"steps":[{"id":"step_1", "tool":route, "task":text,
                 "depends_on":[], "run_if":"always"}],
                "completion_condition":"Eseguire il percorso selezionato; nessuno strumento è stato eseguito."}
    return {"route":route, "score":score, "threshold":threshold,
            "mode":"llm_planner" if fallback else "direct",
            "fallback_reason":"manual_override" if force_llm else ("below_threshold" if fallback else None),
            "router_ms":round(router_ms, 1),
            "total_ms":round((time.perf_counter()-start)*1000, 1), "plan":plan}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--force-llm", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error("La soglia deve essere tra 0 e 1")
    routes, texts = load_inputs(args.data_dir)
    if not 1 <= args.index <= len(texts):
        parser.error("Indice fuori intervallo")
    router = load_router()
    result = run_demo(router, texts[args.index-1], routes, args.threshold, args.force_llm)
    print(json.dumps(result, ensure_ascii=False, indent=2))