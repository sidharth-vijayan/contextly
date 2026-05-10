# Contextly 🤖

> A RAG-based customer support chatbot with WhatsApp-style UI and intelligent human escalation.

Built for the **QuAnHack AI Internship Challenge** — Problem Statement 2: Customer Support Bot.

---

## What it does

- **Train on your docs** — upload any PDF or TXT support document and the bot learns from it instantly
- **Answer L1 queries** — uses RAG (Retrieval-Augmented Generation) to find relevant info and generate clean answers via Groq LLM
- **Score confidence** — every response gets a confidence score based on how relevant the retrieved content is
- **Auto-escalate** — when confidence is too low, automatically creates a support ticket and notifies that a human agent should follow up
- **Manual escalation** — user can say "talk to a human" at any point to instantly create a high-priority ticket
- **Ticket dashboard** — all escalated queries visible in real time under the Tickets tab

---

## Architecture

```
User Message
     ↓
FastAPI Backend
     ↓
┌─────────────────────────────────────┐
│  Escalation Check                   │
│  Did user ask for a human?          │
└──────────────┬──────────────────────┘
               │ No
               ↓
┌─────────────────────────────────────┐
│  RAG Pipeline                       │
│  TF-IDF retrieval over doc chunks   │
│  → Top 3 relevant chunks selected   │
│  → Groq llama-3.1-8b generates      │
│  → Confidence score returned        │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
   High confidence   Low confidence
       │                │
  Return answer    Create ticket
                   + partial answer
                   + flag for human
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI + Python | Fast, async, auto API docs |
| LLM | Groq llama-3.1-8b-instant | Free, extremely fast inference |
| Retrieval | TF-IDF (pure Python) | No dependencies, no model downloads |
| Doc loading | LangChain loaders | Handles PDF + TXT cleanly |
| Frontend | WhatsApp-style HTML/CSS/JS | Familiar UI, zero build step |

---

## Getting Started

### Prerequisites
- Python 3.10+ (3.12 or 3.13 recommended)
- A free Groq API key from [console.groq.com](https://console.groq.com)
- Git

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/sidharth-vijayan/contextly.git
cd contextly
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Activate it:
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4 — Add your Groq API key

Create a file at `backend/.env`:
```
GROQ_API_KEY=gsk_your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com) → API Keys → Create.

### Step 5 — Start the backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Wait for:
```
[RAGEngine] Groq ready. Full RAG mode.
INFO: Application startup complete.
```

### Step 6 — Serve the frontend

Open a **second terminal**, activate the venv, then:

```bash
cd contextly
python -m http.server 3000 --directory frontend
```

### Step 7 — Open the app

Go to `http://localhost:3000` in your browser.

---

## How to use it

1. Click the upload zone in the sidebar → upload `docs_sample/acme_faq.txt` (or your own PDF/TXT)
2. Wait for the bot to confirm it's indexed the document
3. Ask questions in the chat — try these:
   - *"How do I reset my password?"* → confident answer
   - *"What is the refund policy?"* → confident answer
   - *"Who is the CEO?"* → low confidence → auto-escalation
   - *"I want to talk to a human"* → instant manual escalation
4. Click the **Tickets** tab to see all escalated queries with priority levels

---

## Project Structure

```
contextly/
├── .env.example              # API key template
├── .gitignore
├── README.md
├── backend/
│   ├── main.py               # FastAPI routes
│   ├── rag_engine.py         # TF-IDF retrieval + Groq LLM
│   ├── escalation.py         # Ticket creation logic
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html            # WhatsApp-style chat UI
└── docs_sample/
    └── acme_faq.txt          # Sample support document for testing
```

---

## Escalation Logic

| Trigger | Type | Ticket Priority |
|---|---|---|
| User says "talk to human" / "agent" etc. | Manual | High |
| Confidence score too low | Automatic | Medium |

---

## Production Roadmap

- Persistent tickets → PostgreSQL + SQLAlchemy
- Email/Slack alerts → SendGrid / Slack Webhook in `escalation.py`
- WhatsApp interface → Twilio WhatsApp Business API
- Semantic embeddings → swap TF-IDF for vector embeddings when deploying on Linux/cloud
- Cloud deployment → Render (backend) + GitHub Pages (frontend)