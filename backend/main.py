from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from dotenv import load_dotenv
<<<<<<< HEAD
load_dotenv()
=======
load_dotenv()  # reads GROQ_API_KEY from backend/.env
>>>>>>> d86b09709d055620450e8231098d973e8ef38363

from rag_engine import RAGEngine
from escalation import EscalationManager

app = FastAPI(title="Contextly Support Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGEngine()
escalation_manager = EscalationManager()


class ChatRequest(BaseModel):
    session_id: str
    message: str

<<<<<<< HEAD

=======
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
class ChatResponse(BaseModel):
    reply: str
    escalated: bool
    confidence: Optional[float] = None
    ticket_id: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "running",
<<<<<<< HEAD
        "mode": "Full RAG (Groq)" if rag.has_api_key else "Demo mode (keyword search)",
=======
        "mode": "Full RAG (Groq + HuggingFace)" if rag.has_api_key else "Demo mode (no Groq key)",
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
        "docs_loaded": rag.is_ready()
    }


@app.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
<<<<<<< HEAD
        raise HTTPException(status_code=400, detail="Only PDF and TXT supported.")
    content = await file.read()
    result = rag.ingest_document(filename=file.filename, content=content)
    return {"message": f"'{file.filename}' ingested.", "chunks": result["chunks"]}
=======
        raise HTTPException(status_code=400, detail="Only PDF and TXT files supported.")
    content = await file.read()
    result = rag.ingest_document(filename=file.filename, content=content)
    return {"message": f"'{file.filename}' ingested successfully.", "chunks": result["chunks"]}
>>>>>>> d86b09709d055620450e8231098d973e8ef38363


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_msg = request.message.strip()
    session_id = request.session_id

<<<<<<< HEAD
    if escalation_manager.user_wants_human(user_msg):
        ticket = escalation_manager.create_ticket(
            session_id, user_msg, reason="User requested human agent"
        )
        return ChatResponse(
            reply=f"Understood! I've escalated your query to a human agent.\n\nYour ticket ID is **{ticket['id']}**. Someone will reach out shortly.",
=======
    # Check if user explicitly wants a human
    if escalation_manager.user_wants_human(user_msg):
        ticket = escalation_manager.create_ticket(session_id, user_msg, reason="User requested human agent")
        return ChatResponse(
            reply=f"Understood! I've escalated your query to a human agent.\n\nYour ticket ID is **{ticket['id']}**. Someone will reach out to you shortly.",
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
            escalated=True,
            ticket_id=ticket["id"]
        )

<<<<<<< HEAD
    result = rag.query(user_msg) 
    answer = result["answer"]
    confidence = result["confidence"]

    dont_know_phrases = [
            "don't have enough information",
            "i don't have",
            "not enough information",
            "cannot find",
            "no information",
            "i couldn't find",
            "not in the context",
        ]

    groq_doesnt_know = any(phrase in answer.lower() for phrase in dont_know_phrases)

    if confidence < 0.10 or groq_doesnt_know:
=======
    # Query RAG pipeline
    result = rag.query(user_msg)
    answer = result["answer"]
    confidence = result["confidence"]

    # Auto-escalate if confidence is too low
    if confidence < 0.30:
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
        ticket = escalation_manager.create_ticket(session_id, user_msg, reason="Low confidence answer")
        return ChatResponse(
            reply=(
                f"{answer}\n\n"
<<<<<<< HEAD
                f"_(I wasn't fully confident — raised ticket **{ticket['id']}** for a human agent to verify.)_"
=======
                f"_(I wasn't fully confident in this answer. I've raised ticket **{ticket['id']}** "
                f"for a human agent to verify and follow up.)_"
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
            ),
            escalated=True,
            confidence=confidence,
            ticket_id=ticket["id"]
        )

    return ChatResponse(reply=answer, escalated=False, confidence=confidence)


@app.get("/tickets")
def get_tickets():
    return {"tickets": escalation_manager.get_all_tickets()}


<<<<<<< HEAD
@app.get("/docs")
def get_docs():
    return {"docs": rag.get_loaded_docs()}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
=======
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/docs")
def get_docs():
    """Returns list of ingested documents with chunk counts."""
    try:
        collection = rag.vectorstore._collection
        metadatas = collection.get(include=["metadatas"])["metadatas"]
        counts = {}
        for m in metadatas:
            src = m.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        docs = [{"name": name, "chunks": count} for name, count in counts.items()]
        return {"docs": docs}
    except Exception:
        return {"docs": []}
>>>>>>> d86b09709d055620450e8231098d973e8ef38363
