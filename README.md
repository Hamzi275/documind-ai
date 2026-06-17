# DocuMind AI — Multi-Source RAG Research Assistant

Upload PDFs, paste web page URLs, and paste YouTube links — DocuMind AI chunks and
embeds all of it into a local vector database, then lets you chat with an LLM that
retrieves relevant context across every source and cites where each answer came from.

## Run instructions (Windows 11 + VS Code)

### Step 1 — Get a Groq API key

1. Go to [console.groq.com](https://console.groq.com) and sign up (free).
2. Open **API Keys** in the left sidebar and click **Create API Key**.
3. Copy the key — it starts with `gsk_...`. You'll paste it into `.env` in Step 3.

> If you pasted a Groq key into a chat, document, or anywhere public before this,
> revoke it on that same page and generate a new one — treat any exposed key as
> compromised.

### Step 2 — Backend setup

Open this project folder in VS Code, then open a terminal (`` Ctrl+` ``) and run:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

This needs **Python 3.11+**. If `python` isn't recognized, install it from
[python.org](https://python.org) and make sure "Add python.exe to PATH" is checked
during install, then restart the terminal.

The first `pip install` will download `sentence-transformers` and its dependencies
(including PyTorch) — this is a few hundred MB and can take several minutes.

### Step 3 — Create the `.env` file

In the `backend` folder, copy `.env.example` to a new file named `.env`:

```powershell
copy .env.example .env
```

Open `backend\.env` in VS Code and replace the placeholder with your real key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 4 — Run the backend

With the venv still active:

```powershell
uvicorn main:app --reload --port 8000
```

Success looks like this (the first run also pauses briefly while it downloads the
`all-MiniLM-L6-v2` embedding model, roughly 80MB, one time only):

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Leave this terminal running. Open a **second** terminal in VS Code for the frontend.

### Step 5 — Frontend setup

```powershell
cd frontend
npm install
```

This needs **Node.js 18+**. If `npm` isn't recognized, install Node from
[nodejs.org](https://nodejs.org) and restart the terminal.

### Step 6 — Run the frontend

```powershell
npm run dev
```

Success looks like this:

```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

### Step 7 — Test the app

1. Open `http://localhost:5173` in your browser.
2. **PDF tab**: choose any PDF with real text in it (not a scanned image) and upload
   it. A card should appear in the source list with a chunk count.
3. **URL tab**: paste a normal article URL (e.g. a Wikipedia page) and click
   **Add Source**.
4. **YouTube tab**: paste a YouTube link for a video that has captions/subtitles and
   click **Add Source**.
5. In the chat box, ask a question that only one of your sources could answer.
   Confirm the answer streams in word-by-word (not all at once) and that citation
   chips with the source title appear below the answer.

## Common errors & fixes

**1. CORS error in the browser console ("blocked by CORS policy")**
Make sure both servers are running — backend on port 8000, frontend on port 5173 —
and that you're opening `http://localhost:5173`, not `http://127.0.0.1:5173`
(or vice versa) inconsistently. The dev proxy in `vite.config.js` forwards `/api`
calls to the backend, so as long as both are running this should not happen. If it
does, restart both servers.

**2. `chromadb` errors about the persistence path / permissions**
The backend creates a `chroma_db` folder inside `backend/` the first time it runs.
Make sure you started `uvicorn` from inside the `backend` folder (not the project
root) — if you ran it from the wrong folder, delete any stray `chroma_db` folder
that got created in the wrong place and restart from inside `backend`.

**3. First request to `/api/ingest/...` or backend startup is very slow**
The very first time `sentence-transformers` loads `all-MiniLM-L6-v2`, it downloads
the model from Hugging Face (~80MB). This only happens once — it's cached locally
afterward (typically under `C:\Users\<you>\.cache\huggingface`). If it seems stuck,
check your internet connection; if a firewall blocks huggingface.co, the download
will fail with a connection error in the terminal.

**4. `429` errors or chat responses suddenly stop working**
Groq's free tier has rate limits (requests per minute and tokens per day). If you
hit one, the terminal running `uvicorn` will show the Groq error, and the chat
message will show a rate-limit error. Wait a minute and try again, or check your
usage at console.groq.com.

**5. YouTube ingestion fails with "No transcript is available" or similar**
Not every video has captions, and YouTube sometimes blocks automated transcript
requests (rate limiting or region restrictions) — this is an external limitation
of `youtube-transcript-api`, not a bug in this app. Try a different, popular video
with manually-added captions (auto-captions work too, but are less reliable).

**6. `Port 8000` or `Port 5173` already in use**
Something else on your machine is using that port. For the backend, run
`uvicorn main:app --reload --port 8001` instead (and update the `target` in
`frontend/vite.config.js` to `http://127.0.0.1:8001`). For the frontend, Vite will
usually auto-suggest the next free port (e.g. 5174) — just open the URL it prints.

## Project structure

```
documind-ai/
├── backend/        FastAPI + ChromaDB + sentence-transformers + Groq
└── frontend/       React 18 + Vite + Tailwind CSS
```

## Notes on design choices

- Embeddings are computed manually with `sentence-transformers` and passed to
  ChromaDB with `embedding_function=None`, so the model loads exactly once at
  startup (via a singleton `VectorStore`) rather than on every request.
- Each streamed token from Groq is JSON-encoded before being sent over SSE
  (`data: {json.dumps(token)}\n\n`). This is a deliberate correctness fix: LLM
  tokenizers can emit a literal `"\n\n"` as a single token (common for paragraph
  breaks), which — if sent raw — would be indistinguishable from the SSE frame
  delimiter the frontend splits on, silently corrupting the stream. JSON-encoding
  guarantees the token can never collide with the delimiter, and the frontend
  `JSON.parse()`s it back to the original text.
