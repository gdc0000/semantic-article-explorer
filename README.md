# 🧠 Semantic Article Explorer

This project is a full-stack semantic search engine for exploring scientific articles.  
It consists of a React frontend and a FastAPI backend that handles semantic queries using FAISS and SentenceTransformers.


## 📁 Project Structure
---
semantic-article-explorer/
│
├── backend/ # FastAPI entry point
│ └── main.py
│
├── app/ # Core logic modules (used by FastAPI)
│ ├── app.py # FastAPI router (/search)
│ ├── data_manager.py # Loads config, data, model, index
│ ├── search_engine.py # Embedding + FAISS query
│ ├── visualization_engine.py
│
├── frontend/ # Vite + React frontend
│ ├── public/mock_articles.json
│ └── src/components/
│
├── preprocessing/ # Data preparation pipeline
│ ├── 1_clean_data.py
│ ├── 2_generate_embeddings.py
│ ├── 3_build_index.py
│
├── data/ # Processed data files
│ ├── raw_records.json
│ ├── processed_records.parquet
│ ├── embeddings.npy
│ └── faiss_index.faiss
│
├── requirements.txt # Python base deps (torch, faiss, etc.)
├── requirements-backend.txt # FastAPI deps
├── config.yaml # Paths, settings, model type
└── README.md # ← you are here

yaml
Copy
Edit

---

## 🔧 Setup Instructions

### 1. Create and activate the Python virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate
Do this every time you open a new terminal in this project.

2. Install backend requirements
bash
Copy
Edit
pip install -r requirements.txt
pip install -r requirements-backend.txt
3. Install frontend dependencies
bash
Copy
Edit
cd frontend
npm install
```

---

🛠 Preprocessing pipeline (data → embeddings → index)
You must run this pipeline every time you change the raw data.

You can do it in two ways:

✅ A. From notebook (recommended)
In a notebook cell:

python
Copy
Edit
```
import subprocess
import sys

scripts = [
    "preprocessing/1_clean_data.py",
    "preprocessing/2_generate_embeddings.py",
    "preprocessing/3_build_index.py",
]

python_executable = sys.executable  # Use the correct venv
for script in scripts:
    print(f"Running {script}")
    result = subprocess.run([python_executable, script], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

```

✅ B. From terminal
bash
Copy
Edit
```
python preprocessing/1_clean_data.py
python preprocessing/2_generate_embeddings.py
python preprocessing/3_build_index.py
After running all 3, your data/ folder will contain:

processed_records.parquet

embeddings.npy

faiss_index.faiss
```

🚀 Running the app locally
▶ Start backend
From the root folder (with .venv activated):

bash
Copy
Edit
```
python -m uvicorn backend.main:app --reload
```
The backend will be live at: http://localhost:8000

Swagger UI is available at: http://localhost:8000/docs

Default route /search accepts JSON like:

json
Copy
Edit
```
{ "query": "machine learning" }
```
▶ Start frontend
```
cd frontend
npm run dev
```
React app is live at: http://localhost:5173

🧪 Debugging checklist
If you search but see nothing in the UI:

- Is uvicorn running in the terminal?
- Does /search return actual results in http://localhost:8000/docs?
- Do the records in processed_records.parquet contain title and abstract?
- Is the number of vectors in embeddings.npy the same as the number of records?
- Is the FAISS index size the same?
- Is React fetching from http://localhost:8000/search and not something else?

Use browser DevTools (F12) → Network tab → check POST /search.

🌐 Optional: Redirect root to /docs
To avoid 404 when visiting http://localhost:8000, you can add this to main.py:

```
from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse("/docs")

```
✅ Ready for deploy?
If everything works locally and you want to deploy to Render or another host, ask yourself:

Is the app self-contained (no Streamlit leftovers)?

Is config.yaml portable?

Is CORS enabled correctly in main.py?

Let’s ship it. 🚀

*Last updated: 2025-06-08*