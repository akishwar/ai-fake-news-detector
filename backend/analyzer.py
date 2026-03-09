"""NLP analysis pipeline for fake news detection using Google Gemini API.

Combines Gemini AI reasoning with deep heuristic analysis for comprehensive
fake news detection.
"""

import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
from utils.preprocessor import (
    clean_text,
    compute_clickbait_score,
    compute_subjectivity_score,
    compute_vague_attribution_score,
    compute_hedging_score,
    compute_specificity_score,
    compute_ai_generation_score,
    compute_credibility_signals_score,
    detect_red_flags,
    extract_keywords,
    compute_linguistic_features,
)

# ── Load environment & configure Gemini ─────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY and GEMINI_API_KEY != "PASTE_YOUR_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    GEMINI_LOADED = True
    print("✅ Gemini API configured successfully!")
else:
    model = None
    GEMINI_LOADED = False
    print("⚠️  No Gemini API key found. Using heuristic-only analysis.")
    print("   Set GEMINI_API_KEY in backend/.env to enable AI analysis.")


# ── Gemini Prompt ───────────────────────────────────────────────────────────
ANALYSIS_PROMPT = """You are an expert fact-checker and media analyst. Analyze the following news article for authenticity and credibility.

Evaluate these specific aspects:
1. **Source credibility**: Are specific, named, verifiable sources cited? Or does it rely on vague attributions like "reportedly", "sources say", "officials familiar with"?
2. **Verifiable claims**: Does the article contain specific, falsifiable claims with dates, numbers, and named individuals? Or is it full of vague, unverifiable statements?
3. **Writing patterns**: Does the text show signs of AI generation (formulaic structure, excessive hedging, overly smooth prose, no direct quotes)?
4. **Logical consistency**: Are the claims internally consistent and plausible?
5. **Red flags**: Clickbait language, emotional manipulation, conspiracy theories, lack of attribution?

IMPORTANT: A well-written article that uses phrases like "reportedly", "officials say", "if successful", "may later be expanded" WITHOUT naming specific people or providing direct quotes is LIKELY FABRICATED, even if it sounds professional.

Respond ONLY with a valid JSON object in this exact format (no markdown, no explanation):
{
    "credibility_score": <number 0-100, where 100 is fully credible>,
    "label": "<Likely Real OR Uncertain OR Likely Fake>",
    "reasoning": "<2-3 sentence explanation of your assessment>",
    "source_quality": "<high OR medium OR low OR none>",
    "ai_generated_likelihood": "<high OR medium OR low>",
    "key_concerns": ["<concern 1>", "<concern 2>"]
}

Article to analyze:
\"\"\"
{article_text}
\"\"\"
"""


def _get_sentiment(text: str) -> tuple[str, float]:
    """Simple rule-based sentiment analysis."""
    positive_words = {
        "good", "great", "excellent", "positive", "success", "improve",
        "benefit", "progress", "hope", "support", "growth", "healthy",
        "safe", "effective", "proven", "confirmed", "achievement",
    }
    negative_words = {
        "bad", "terrible", "awful", "negative", "fail", "danger",
        "threat", "crisis", "fear", "death", "kill", "attack",
        "destroy", "corrupt", "fraud", "scam", "lie", "fake",
        "disaster", "catastrophe", "alarming", "horrific",
    }

    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    pos = len(words & positive_words)
    neg = len(words & negative_words)
    total = pos + neg

    if total == 0:
        return "neutral", 0.5
    ratio = pos / total
    if ratio > 0.6:
        return "positive", round(ratio, 2)
    elif ratio < 0.4:
        return "negative", round(1 - ratio, 2)
    return "neutral", 0.5


def _extract_entities(text: str) -> list[str]:
    """Extract named entities using simple capitalization heuristics."""
    patterns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
    stop_starts = {"The", "This", "That", "These", "Those", "It", "He", "She",
                   "They", "We", "You", "I", "A", "An", "In", "On", "At",
                   "For", "But", "And", "Or", "So", "If", "When", "While",
                   "After", "Before", "However", "Moreover", "Also", "Many",
                   "Some", "All", "New", "Here", "There", "According"}
    entities = list(dict.fromkeys(
        e for e in patterns if e.split()[0] not in stop_starts and len(e) > 2
    ))
    return entities[:10]


async def _call_gemini(text: str) -> dict | None:
    """Call Gemini API for AI-powered analysis."""
    if not GEMINI_LOADED or not model:
        return None

    try:
        prompt = ANALYSIS_PROMPT.replace("{article_text}", text[:3000])
        response = model.generate_content(prompt)

        # Parse JSON from response
        response_text = response.text.strip()
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[-1]
            response_text = response_text.rsplit("```", 1)[0]
        response_text = response_text.strip()

        result = json.loads(response_text)
        return result
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


async def analyze_text(text: str) -> dict:
    """
    Run the full analysis pipeline combining Gemini AI with heuristic analysis.
    """
    cleaned = clean_text(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 1: Gemini AI Analysis
    # ══════════════════════════════════════════════════════════════════════
    gemini_result = await _call_gemini(cleaned)
    gemini_score = None
    gemini_concerns = []

    if gemini_result:
        gemini_score = gemini_result.get("credibility_score", 50)
        gemini_concerns = gemini_result.get("key_concerns", [])
        gemini_reasoning = gemini_result.get("reasoning", "")
        gemini_source_quality = gemini_result.get("source_quality", "medium")
        gemini_ai_likelihood = gemini_result.get("ai_generated_likelihood", "low")

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 2-7: Heuristic Analysis (same as before)
    # ══════════════════════════════════════════════════════════════════════
    vague_score, vague_matches = compute_vague_attribution_score(text)
    hedging_score, hedging_count = compute_hedging_score(text)
    specificity_score, specificity_details = compute_specificity_score(text)
    ai_score, ai_matches = compute_ai_generation_score(text)
    credibility_signal_score, credibility_signals = compute_credibility_signals_score(text)
    clickbait = compute_clickbait_score(text)
    subjectivity = compute_subjectivity_score(text)
    sentiment_label, sentiment_score = _get_sentiment(text)
    red_flags = detect_red_flags(text)
    keywords = extract_keywords(text)
    entities = _extract_entities(text)
    linguistic = compute_linguistic_features(text)

    # ══════════════════════════════════════════════════════════════════════
    # COMPOSITE CREDIBILITY SCORE
    # ══════════════════════════════════════════════════════════════════════
    word_count = linguistic.get("word_count", len(text.split()))

    # --- Heuristic penalty calculation ---
    # Vague attribution: only penalize if article actually uses vague sourcing
    vague_penalty = vague_score * 0.20

    # Hedging: only penalize if density is notable
    hedging_penalty = hedging_score * 0.12

    # Specificity: scale penalty by article length
    # Short articles (< 100 words) naturally have fewer details — don't punish them
    length_factor = min(word_count / 150.0, 1.0)  # full penalty only for 150+ word articles
    specificity_penalty = (1.0 - specificity_score) * 0.12 * length_factor

    # AI generation patterns
    ai_penalty = ai_score * 0.12

    # Traditional signals
    clickbait_penalty = clickbait * 0.10
    subjectivity_penalty = subjectivity * 0.05
    caps_penalty = min(linguistic.get("caps_ratio", 0) * 3, 1.0) * 0.05

    # Red flags: only from genuine red flags, not all warnings
    genuine_flags = [f for f in red_flags if not f.startswith("🤖")]
    red_flag_penalty = min(len(genuine_flags) / 5.0, 1.0) * 0.08

    total_penalty = (
        vague_penalty + hedging_penalty + specificity_penalty +
        ai_penalty + clickbait_penalty + subjectivity_penalty +
        caps_penalty + red_flag_penalty
    )

    # --- Bonus signals ---
    credibility_bonus = credibility_signal_score * 0.12
    specificity_bonus = specificity_score * 0.10

    # Named entity bonus: articles with real named people/places are more credible
    named_entity_bonus = min(len(entities) / 4.0, 1.0) * 0.10

    # Short article leniency: brief news snippets shouldn't be penalized
    short_article_bonus = max(0, (1.0 - word_count / 100.0)) * 0.08 if word_count < 100 else 0

    total_bonus = credibility_bonus + specificity_bonus + named_entity_bonus + short_article_bonus

    heuristic_assessment = 0.5 - total_penalty + total_bonus
    heuristic_assessment = max(0.0, min(1.0, heuristic_assessment))
    heuristic_pct = heuristic_assessment * 100

    # --- Blend Gemini + Heuristics ---
    if gemini_score is not None:
        # Gemini (65%) + Heuristics (35%) — Gemini understands context better
        credibility_pct = round(gemini_score * 0.65 + heuristic_pct * 0.35, 1)
        model_confidence = 0.85
    else:
        credibility_pct = round(heuristic_pct, 1)
        model_confidence = 0.50

    credibility_pct = max(5.0, min(95.0, credibility_pct))

    # ═══════════════════════════════════════════════════════════════════════
    # LABEL & SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    if credibility_pct >= 70:
        label = "Likely Real"
    elif credibility_pct >= 40:
        label = "Uncertain"
    else:
        label = "Likely Fake"

    # Add Gemini concerns to red flags
    if gemini_concerns:
        for concern in gemini_concerns:
            if concern and concern not in red_flags:
                red_flags.append(f"🤖 {concern}")

    # Build summary
    summary_parts = []
    if gemini_result and gemini_reasoning:
        summary_parts.append(gemini_reasoning)
    else:
        if credibility_pct >= 70:
            summary_parts.append("This article appears to be credible based on our analysis.")
        elif credibility_pct >= 40:
            summary_parts.append("This article shows mixed credibility signals and should be verified.")
        else:
            summary_parts.append("This article contains multiple indicators of unreliable or fabricated content.")

    if len(red_flags) > 0:
        summary_parts.append(f"We detected {len(red_flags)} warning signal(s).")
    if vague_score >= 0.5:
        summary_parts.append("The article relies heavily on vague, unnamed sources.")
    if ai_score >= 0.5:
        summary_parts.append("Text patterns suggest possible AI-generated content.")

    return {
        "credibility_score": credibility_pct,
        "label": label,
        "confidence": round(model_confidence, 2),
        "summary": " ".join(summary_parts),
        "insights": {
            "sentiment": sentiment_label,
            "sentiment_score": round(sentiment_score, 2),
            "clickbait_score": round(clickbait, 2),
            "subjectivity_score": round(subjectivity, 2),
            "entities": entities,
            "keywords": keywords,
            "red_flags": red_flags,
            "linguistic_features": linguistic,
        },
    }
