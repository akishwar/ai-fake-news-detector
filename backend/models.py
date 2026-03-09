"""Pydantic request/response schemas for the Fake News Detection API."""

from pydantic import BaseModel, Field
from typing import Optional


class AnalysisRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""
    text: str = Field(..., min_length=10, description="News article text to analyze")


class InsightData(BaseModel):
    """Detailed insights from the NLP analysis."""
    sentiment: str = Field(..., description="Overall sentiment: positive, negative, or neutral")
    sentiment_score: float = Field(..., description="Sentiment confidence (0-1)")
    clickbait_score: float = Field(..., description="Clickbait probability (0-1)")
    subjectivity_score: float = Field(..., description="Subjectivity score (0-1)")
    entities: list[str] = Field(default_factory=list, description="Named entities found")
    keywords: list[dict] = Field(default_factory=list, description="Top keywords with weights")
    red_flags: list[str] = Field(default_factory=list, description="Warning signals detected")
    linguistic_features: dict = Field(default_factory=dict, description="Linguistic analysis data")


class AnalysisResponse(BaseModel):
    """Response body from the /api/analyze endpoint."""
    credibility_score: float = Field(..., description="Overall credibility score (0-100)")
    label: str = Field(..., description="Human-readable label: Likely Fake, Uncertain, Likely Real")
    confidence: float = Field(..., description="Model confidence (0-1)")
    insights: InsightData
    summary: str = Field(..., description="Brief explanation of the analysis")
