import os
import tempfile
import math
from collections import Counter
from groq import Groq

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader


class RAGEngine:
    """
    RAG pipeline — no local models, no embedding APIs.
    - Retrieval : TF-IDF similarity (pure Python, zero dependencies)
    - LLM       : Groq llama-3.1-8b-instant
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        self.has_api_key = bool(api_key and api_key.startswith("gsk_"))

        if self.has_api_key:
            self.client = Groq(api_key=api_key)
            print("[RAGEngine] Groq ready. Full RAG mode.")
        else:
            self.client = None
            print("[RAGEngine] No Groq key. Demo mode.")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )

        # In-memory store
        self._chunks = []

    def is_ready(self) -> bool:
        return len(self._chunks) > 0

    def ingest_document(self, filename: str, content: bytes) -> dict:
        suffix = ".pdf" if filename.endswith(".pdf") else ".txt"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        loader = (
            PyPDFLoader(tmp_path)
            if filename.endswith(".pdf")
            else TextLoader(tmp_path, encoding="utf-8")
        )

        raw_docs = loader.load()

        for doc in raw_docs:
            doc.metadata["source"] = filename

        chunks = self.splitter.split_documents(raw_docs)

        os.unlink(tmp_path)

        # Remove old chunks from same file
        self._chunks = [
            c for c in self._chunks
            if c["source"] != filename
        ]

        for chunk in chunks:
            self._chunks.append({
                "text": chunk.page_content,
                "source": filename
            })

        print(f"[RAGEngine] '{filename}' -> {len(chunks)} chunks indexed.")

        return {
            "chunks": len(chunks),
            "source": filename
        }

    def _tfidf_score(self, query: str, doc: str) -> float:
        def tokenize(text):
            return text.lower().split()

        q_tokens = tokenize(query)
        d_tokens = tokenize(doc)

        d_counter = Counter(d_tokens)
        d_len = len(d_tokens)

        score = 0.0
        N = len(self._chunks) + 1

        for term in set(q_tokens):
            tf = d_counter.get(term, 0) / max(d_len, 1)

            doc_freq = sum(
                1 for c in self._chunks
                if term in c["text"].lower()
            )

            idf = math.log((N + 1) / (doc_freq + 1)) + 1

            score += tf * idf

        return score

    def query(self, question: str) -> dict:
        if not self.is_ready():
            return {
                "answer": "No documents loaded yet.",
                "confidence": 0.0,
                "sources": []
            }

        scored = [
            (self._tfidf_score(question, c["text"]), c)
            for c in self._chunks
        ]

        scored.sort(key=lambda x: x[0], reverse=True)

        top3 = scored[:3]

        top_score = top3[0][0]

        all_scores = [s for s, _ in scored if s > 0]
        max_score = max(all_scores) if all_scores else 1.0

        confidence = (
            round(top_score / max_score, 3)
            if max_score > 0 else 0.0
        )

        context = "\n\n".join([
            c["text"] for _, c in top3
        ])

        sources = list(set([
            c["source"] for _, c in top3
        ]))

        if self.has_api_key:
            prompt = f"""
You are a helpful customer support assistant.

Answer the customer's question using ONLY the information in the context below.

If the answer is not in the context, say:
"I don't have enough information on this topic."

Context:
{context}

Customer question:
{question}

Answer:
"""

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            return {
                "answer": response.choices[0].message.content.strip(),
                "confidence": confidence,
                "sources": sources
            }

        return {
            "answer": top3[0][1]["text"].strip(),
            "confidence": confidence,
            "sources": sources
        }

    def get_loaded_docs(self) -> list:
        counts = {}

        for chunk in self._chunks:
            counts[chunk["source"]] = (
                counts.get(chunk["source"], 0) + 1
            )

        return [
            {
                "name": k,
                "chunks": v
            }
            for k, v in counts.items()
        ]
