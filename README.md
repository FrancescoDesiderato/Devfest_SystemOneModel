# Devfest Talk: System One Model 💡

Repository del codice per il talk GDG DevFest 2026 dedicato ai **System One Models**.

## Panoramica

Mission Control dimostra un flusso ibrido di routing e pianificazione:

1. Un decision model multilingue classifica la richiesta in una route predefinita.
2. Il codice applicativo confronta lo score con una soglia configurabile.
3. Se lo score è maggiore o uguale alla soglia, prepara un piano con un solo percorso.
4. Se lo score è inferiore alla soglia, chiama un LLM generativo per produrre un piano strutturato, eventualmente composto da più passaggi.

Un override manuale esplicito permette anche di forzare il planner per confrontare i due comportamenti.

```text
Richiesta dell'utente
        |
        v
GLiNER multilingue — CPU
        |
        v
Gate applicativo
        |
        +-- score >= soglia --> Piano con route diretta
        |
        +-- score < soglia ---> LLM planner --> Piano multi-step
```

La demo produce piani, ma non esegue gli strumenti

## Modelli e ambienti

| Componente | Versione locale | Google Colab |
| --- | --- | --- |
| Decision model | `fastino/GLiNER2.5-multi-Decide`, CPU | Stesso modello, CPU |
| LLM planner | `gemma3:4b` tramite Ollama | `google/gemma-3-4b-it` tramite Transformers, GPU |
| Interfaccia | Streamlit o terminale | Widget del notebook |

Entrambe le configurazioni scaricano i pesi nei rispettivi ambienti. La cache di Colab e quella locale non sono condivise automaticamente.

Il tag Ollama e il modello Hugging Face in FP16 utilizzano rappresentazioni dei pesi e configurazioni di inferenza differenti: non è garantito che producano risposte identiche.

## Struttura del progetto

I comandi seguenti assumono questa organizzazione. Adattare i percorsi se i file vengono spostati o rinominati.

```text
Devfest_SystemOneModel/
├── README.md
├── requirements.txt
├── app.py
├── llm_planner_local.py
├── mission_control_colab_huggingface.ipynb
└── llm_planner/
    ├── routes.json
    └── cases.txt
```

`app.py` importa `load_router`, `route_request` e `llm_plan` da `llm_planner_local.py`. I due file Python devono quindi rimanere nella stessa cartella, salvo modifiche agli import.

## Esecuzione in locale

### 1. Creare un ambiente Python

Come punto di partenza si consiglia Python 3.11.

```bash
python3.11 -m venv .venv
```

Attivazione su macOS/Linux:

```bash
source .venv/bin/activate
```

Attivazione su Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Installare le dipendenze:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

### 2. Installare e avviare Ollama

Installare Ollama separatamente seguendo le istruzioni per il proprio sistema operativo:

https://ollama.com/download

Scaricare il modello del planner:

```bash
ollama pull gemma3:4b
```

Se il server non è già attivo, avviarlo in un altro terminale:

```bash
ollama serve
```

Il backend si collega al seguente indirizzo:

```text
http://127.0.0.1:11434
```

Modello e indirizzo sono configurati in `llm_planner_local.py`:

```python
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_URL = "http://127.0.0.1:11434"
```

Non serve una chiave API OpenAI. Non serve neppure il pacchetto Python `ollama`: il codice comunica con il server tramite `requests`.

### 3. Avviare l'interfaccia grafica

Dalla cartella principale del repository:

```bash
python -m streamlit run app.py
```

Aprire nel browser l'indirizzo mostrato da Streamlit.

Nella barra laterale:

1. Scegliere tra file locali e caricamento diretto.
2. Se si usano file locali, selezionare la cartella dei dati e i file JSON/TXT.
3. Impostare la soglia di escalation.
4. Facoltativamente, attivare l'override manuale per forzare l'LLM.

Nel pannello principale:

1. Selezionare un caso.
2. Modificare eventualmente il testo.
3. Avviare la demo.
4. Osservare il percorso evidenziato, lo score, i tempi e il piano finale.
5. Esaminare il grafo delle dipendenze e il JSON.
6. Esportare il risultato, se necessario.

Quando cambiano input o configurazione occorre eseguire nuovamente la demo: l'interfaccia non presenta un risultato precedente come se appartenesse alla nuova richiesta.

### 4. Eseguire da terminale

Primo caso:

```bash
python llm_planner_local.py --index 1 --threshold 0.8
```

Caso composto:

```bash
python llm_planner_local.py --index 5 --threshold 0.8
```

Planner forzato per confronto:

```bash
python llm_planner_local.py --index 5 --force-llm
```

Cartella di base alternativa:

```bash
python llm_planner_local.py --data-dir /percorso/del/progetto --index 5
```

Nel backend attuale `--data-dir` indica la cartella che contiene `llm_planner/`, non direttamente la cartella dei file JSON e TXT. Gli indici dei casi partono da 1.

## Esecuzione su Google Colab

Aprire `mission_control_colab_huggingface.ipynb`. Questa versione utilizza direttamente Hugging Face Transformers: non richiede Ollama, server aggiuntivi o chiamate a `subprocess`.

### 1. Preparare l'accesso a Hugging Face

1. Accedere al proprio account Hugging Face.
2. Aprire https://huggingface.co/google/gemma-3-4b-it e accettare le condizioni di accesso al modello.
3. Creare un token con permesso di lettura dei file del modello.
4. Autenticarsi con lo stesso account quando il notebook esegue `notebook_login()`.

Non inserire token nel repository, nelle celle condivise o negli output salvati.

### 2. Selezionare un runtime GPU

Attivare un runtime GPU prima di caricare Gemma. Il notebook mostra dispositivo e memoria disponibili.

GLiNER viene eseguito sulla CPU; Gemma viene caricato sulla GPU in FP16. La disponibilità delle risorse e una quantità sufficiente di VRAM non sono garantite.

### 3. Caricare i file ed eseguire la demo

Quando richiesto, caricare esattamente:

- Un file JSON con le route, per esempio `routes.json`.
- Un file TXT con i casi, per esempio `cases.txt`.

Il notebook identifica i file in base all'estensione: non è necessario mantenere questi nomi.

Eseguire prima la cella che misura gli score dei cinque casi. Successivamente caricare Gemma e usare i widget per scegliere il caso, modificare il testo, impostare la soglia e osservare il piano.

### Gestione della memoria

Il notebook colloca esplicitamente Gemma sulla GPU, senza spostarne automaticamente una parte sulla CPU. In caso di memoria insufficiente, usare risorse più adatte oppure modificare il caricamento per adottare un modello più piccolo o la quantizzazione. Queste alternative non vengono abilitate automaticamente.

Lo spazio della VM Colab è temporaneo. Se la cache viene persa quando la VM viene ripristinata o sostituita, sarà necessario riscaricare i pesi.

## Formato dei dati

### JSON delle route

```json
{
  "routes": [
    {
      "id": "knowledge_base",
      "description": "Consulta documenti e policy aziendali interne."
    },
    {
      "id": "web_search",
      "description": "Cerca informazioni esterne aggiornate e relative fonti."
    },
    {
      "id": "calculator",
      "description": "Esegue calcoli quando dati e regole sono già disponibili."
    },
    {
      "id": "clarification",
      "description": "Chiede informazioni essenziali mancanti per richieste ambigue."
    }
  ]
}
```

`llm_planner` non è una quinta classe del router: è il fallback attivato dalla logica applicativa.

### TXT dei casi

Usare la codifica UTF-8 e separatori numerati:

```text
=== TESTO 01 ===
Secondo la policy aziendale, quali documenti servono per il rimborso?

=== TESTO 02 ===
Qual è il cambio EUR/USD attuale? Indica fonte e orario.
```

I cinque scenari della demo riguardano:

1. Consultazione di una policy interna.
2. Ricerca di un cambio aggiornato.
3. Calcolo aritmetico.
4. Richiesta incompleta che necessita di chiarimento.
5. Pianificazione multi-step di un rimborso per una trasferta.

Il quinto caso combina policy, cambio GBP/EUR, commissioni e rimborso. Se la policy risultasse incompleta, il piano dovrebbe includere un chiarimento condizionale.

## Output del planner

Il piano utilizza questa struttura:

```json
{
  "steps": [
    {
      "id": "step_1",
      "tool": "knowledge_base",
      "task": "Recupera il massimale rimborsabile e le regole sulle commissioni.",
      "depends_on": [],
      "run_if": "always"
    }
  ],
  "completion_condition": "Le regole necessarie sono state recuperate o chiarite."
}
```

L'esempio illustra il formato, non un piano completo per il quinto caso.

## Risorse

- GLiNER multilingue: https://huggingface.co/fastino/GLiNER2.5-multi-Decide
- Gemma su Hugging Face: https://huggingface.co/google/gemma-3-4b-it
- Gemma su Ollama: https://ollama.com/library/gemma3:4b
- Documentazione Streamlit: https://docs.streamlit.io/

