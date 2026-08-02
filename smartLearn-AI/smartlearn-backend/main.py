import sys
from pathlib import Path

# Allow Python to import from this hyphenated package directory
sys.path.insert(0, str(Path(__file__).parent))

import os
import re

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from services.llm import answer_from_pages
from services.pdf import extract_pages

app = FastAPI(title="SmartLearn Lite API")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

documents: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    chat_id: str = "day2-demo"
    message: str = Field(min_length=2, max_length=2000)


@app.get("/")
def root():
    return {"message": "SmartLearn Lite API is running"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/upload")
async def upload(
    chat_id: str = Query(...),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    try:
        pages = extract_pages(pdf_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    total = sum(len(p["text"]) for p in pages)
    if total == 0:
        raise HTTPException(422, "No readable text found — OCR is not supported")

    documents[chat_id] = pages

    return {
        "status": "ok",
        "filename": file.filename,
        "pages": len(pages),
        "characters": total,
    }


@app.post("/chat")
def chat(body: ChatRequest):
    pages = documents.get(body.chat_id)
    if pages is None:
        raise HTTPException(
            404,
            f"No PDF uploaded for chat_id '{body.chat_id}'. Upload a PDF via POST /upload first.",
        )

    try:
        answer = answer_from_pages(pages, body.message)
    except Exception as e:
        raise HTTPException(502, f"LLM call failed: {e}")

    all_page_numbers = {p["page"] for p in pages}
    cited = {
        int(n) for n in re.findall(r"\[Page\s*(\d+)\]", answer) if int(n) in all_page_numbers
    }

    return {
        "answer": answer,
        "citations": sorted(cited),
    }