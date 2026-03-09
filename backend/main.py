"""FastAPI application entry point for Fake News Detection API."""

import os
import io
import json
import base64
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from models import AnalysisRequest, AnalysisResponse
from analyzer import analyze_text

load_dotenv()

app = FastAPI(
    title="Fake News Detection API",
    description="AI-powered platform to analyze news articles for credibility",
    version="1.0.0",
)

# ── CORS (allow frontend dev server) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "fake-news-detector"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_article(request: AnalysisRequest):
    """Analyze a news article and return credibility assessment."""
    try:
        result = await analyze_text(request.text)
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/extract-text")
async def extract_text_from_file(file: UploadFile = File(...)):
    """Extract text from uploaded PDF or image file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename.lower()
    content = await file.read()

    try:
        # ── PDF extraction ──
        if filename.endswith(".pdf"):
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            extracted = "\n".join(text_parts).strip()
            if not extracted:
                raise HTTPException(status_code=400, detail="Could not extract text from PDF. The PDF may be image-based — try uploading as an image instead.")
            return {"text": extracted, "source": "pdf", "pages": len(reader.pages)}

        # ── Image extraction (via Gemini Vision) ──
        elif filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
                raise HTTPException(status_code=500, detail="Gemini API key not configured for image OCR")

            genai.configure(api_key=api_key)
            vision_model = genai.GenerativeModel("gemini-2.0-flash")

            # Prepare image for Gemini
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            response = vision_model.generate_content([
                "Extract ALL text from this image exactly as written. Return ONLY the extracted text, nothing else. If there is no readable text, respond with 'NO_TEXT_FOUND'.",
                img
            ])

            extracted = response.text.strip()
            if extracted == "NO_TEXT_FOUND" or not extracted:
                raise HTTPException(status_code=400, detail="No readable text found in the image.")
            return {"text": extracted, "source": "image"}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, JPG, or PNG file.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
