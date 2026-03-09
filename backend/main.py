"""FastAPI application entry point for Fake News Detection API."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AnalysisRequest, AnalysisResponse
from analyzer import analyze_text

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
        result = analyze_text(request.text)
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
