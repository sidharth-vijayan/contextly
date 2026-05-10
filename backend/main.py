from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from dotenv import load_dotenv

load_dotenv()

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


class ChatResponse(BaseModel):
    reply: str
    escalated: bool
    confidence: Optional[float] = None
    ticket_id: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "running",
        "mode": "Full RAG (Groq)"
        if rag.has_api_key
        else "Demo mode (keyword search)",
        "docs_loaded": rag.is_ready()
    }


@app.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT supported."
        )

    content = await file.read()

    result = rag.ingest_document(
        filename=file.filename,
        content=content
    )

    return {
        "message": f"'{file.filename}' ingested.",
        "chunks": result["chunks"]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    user_msg = request.message.strip()
    session_id = request.session_id

    # Manual escalation
    if escalation_manager.user_wants_human(user_msg):

        ticket = escalation_manager.create_ticket(
            session_id,
            user_msg,
            reason="User requested human agent"
        )

        return ChatResponse(
            reply=(
                "Understood! I've escalated your query "
                "to a human agent.\n\n"
                f"Your ticket ID is **{ticket['id']}**."
            ),
            escalated=True,
            ticket_id=ticket["id"]
        )

    # Query RAG
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

    groq_doesnt_know = any(
        phrase in answer.lower()
        for phrase in dont_know_phrases
    )

    # Auto escalation
    if confidence < 0.10 or groq_doesnt_know:

        ticket = escalation_manager.create_ticket(
            session_id,
            user_msg,
            reason="Low confidence answer"
        )

        return ChatResponse(
            reply=(
                f"{answer}\n\n"
                f"_(Low confidence detected. "
                f"Raised ticket **{ticket['id']}** "
                f"for human review.)_"
            ),
            escalated=True,
            confidence=confidence,
            ticket_id=ticket["id"]
        )

    return ChatResponse(
        reply=answer,
        escalated=False,
        confidence=confidence
    )


@app.get("/tickets")
def get_tickets():
    return {
        "tickets": escalation_manager.get_all_tickets()
    }


@app.get("/docs")
def get_docs():
    return {
        "docs": rag.get_loaded_docs()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
