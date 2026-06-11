# PDC RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** based chatbot for the Parallel & Distributed Computing (PDC) course.

## 🚀 Features
- **Parallelized TF-IDF Search** using Python `multiprocessing` (ProcessPoolExecutor)
- **Google Gemini 2.5 Flash API** integration for smart academic answers
- **Offline Extractive Fallback** — works without any API key
- **Performance Benchmarking Dashboard** with live speedup charts (Sequential vs. Parallel)
- **Active CPU Core Visualizer**
- **Premium Glassmorphic Web UI** (dark mode, Chart.js, animations)

## 🗂️ Project Structure
```
pdc CCP/
├── app.py                  # Flask backend server
├── rag_engine.py           # Parallel TF-IDF indexer and retrieval engine
├── requirements.txt        # Python dependencies
├── run_app.bat             # Windows one-click launcher
├── .env                    # Gemini API key config (add your key here)
│
├── knowledge_base/         # PDC course notes (6 topic files)
│   ├── 01_intro_parallel.md
│   ├── 02_laws_metrics.md
│   ├── 03_shared_memory.md
│   ├── 04_distributed_mem.md
│   ├── 05_gpus_cuda.md
│   └── 06_dist_systems.md
│
├── templates/
│   └── index.html          # Dashboard HTML
└── static/
    ├── css/style.css       # Glassmorphism styling
    └── js/app.js           # Frontend logic + Chart.js
```

## ⚙️ Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/Roopchand415/Rag-Chatbot-PDC.git
cd Rag-Chatbot-PDC
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Add your Gemini API Key
Open `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_key_here
```
> Get a free key at: https://aistudio.google.com/

### 4. Run the server
```bash
python app.py
```
Or double-click `run_app.bat` on Windows.

### 5. Open in browser
```
http://127.0.0.1:5000
```

## 💡 How the RAG Engine Works
1. **Document Loading** — Reads `.md` files from `knowledge_base/` and splits into chunks.
2. **Parallel Indexing** — Computes TF-IDF vectors across CPU cores using `ProcessPoolExecutor`.
3. **Parallel Search** — Calculates Cosine Similarity for each query in parallel.
4. **Context Augmentation** — Top matching chunks are sent as context to Gemini API.
5. **Answer Generation** — Gemini generates a clear academic response (or falls back to extractive summaries).

## 📊 PDC Concepts Demonstrated
| Concept | Implementation |
|---------|---------------|
| Parallel Processing | ProcessPoolExecutor for TF-IDF + Search |
| Amdahl's Law | Benchmark slider (Low vs. Heavy workload) |
| Speedup & Efficiency | Live dashboard metrics (Sp, Ep) |
| Process Communication | IPC via Python multiprocessing |
| Task Decomposition | Chunk-level parallel similarity matching |

## 👨‍💻 Created By
**ROOP CHAND**
Parallel & Distributed Computing (PDC) — 2026
