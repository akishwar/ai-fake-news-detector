"""NLP analysis pipeline for fake news detection.

Enhanced with deep multi-signal analysis to catch well-written AI-generated
fake news, not just clickbait/sensational content.
"""

import re
from transformers import pipeline
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

# ── Load the pre-trained model once at startup ──────────────────────────────
print("⏳ Loading fake news classification model...")
try:
    classifier = pipeline(
        "text-classification",
        model="hamzab/roberta-fake-news-classification",
        top_k=None,
    )
    MODEL_LOADED = True
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"⚠️  Model loading failed: {e}")
    print("   Falling back to heuristic-only analysis.")
    classifier = None
    MODEL_LOADED = False


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


def analyze_text(text: str) -> dict:
    """
    Run the full NLP analysis pipeline on the given text.

    Uses a multi-signal approach:
    1. ML model prediction (RoBERTa fine-tuned on fake news)
    2. Vague attribution detection
    3. Hedging/uncertainty language analysis
    4. Specificity analysis (quotes, named sources, data, dates)
    5. AI-generated content pattern detection
    6. Credibility signal verification
    7. Traditional heuristics (clickbait, subjectivity, caps, emotional language)

    The final credibility score is a weighted combination of all signals.
    """
    cleaned = clean_text(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 1: ML Model Prediction
    # ══════════════════════════════════════════════════════════════════════
    model_score = 0.5
    model_confidence = 0.5

    if MODEL_LOADED and classifier:
        try:
            input_text = cleaned[:2048]
            result = classifier(input_text)
            if result and isinstance(result[0], list):
                scores_dict = {item['label'].lower(): item['score'] for item in result[0]}
            elif result:
                scores_dict = {item['label'].lower(): item['score'] for item in result}
            else:
                scores_dict = {}

            real_score = scores_dict.get('real', scores_dict.get('true', scores_dict.get('1', 0.5)))
            fake_score = scores_dict.get('fake', scores_dict.get('false', scores_dict.get('0', 0.5)))
            model_score = real_score
            model_confidence = max(real_score, fake_score)
        except Exception as e:
            print(f"Prediction error: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 2: Vague Attribution (CRITICAL for well-written fake news)
    # ══════════════════════════════════════════════════════════════════════
    vague_score, vague_matches = compute_vague_attribution_score(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 3: Hedging / Uncertainty Language
    # ══════════════════════════════════════════════════════════════════════
    hedging_score, hedging_count = compute_hedging_score(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 4: Specificity (verifiable details)
    # ══════════════════════════════════════════════════════════════════════
    specificity_score, specificity_details = compute_specificity_score(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 5: AI-Generated Content Detection
    # ══════════════════════════════════════════════════════════════════════
    ai_score, ai_matches = compute_ai_generation_score(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 6: Credibility Signals (legitimate journalism markers)
    # ══════════════════════════════════════════════════════════════════════
    credibility_signal_score, credibility_signals = compute_credibility_signals_score(text)

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL 7: Traditional Heuristics
    # ══════════════════════════════════════════════════════════════════════
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
    #
    # Strategy: Start with model score, then apply penalties & bonuses
    # from all heuristic signals. Well-written fake articles will get
    # penalized for vague sourcing, hedging, lack of specificity, and
    # AI patterns even if the model is fooled.

    # --- Penalty signals (each reduces credibility) ---
    # Vague attribution is the #1 indicator for fabricated news
    vague_penalty = vague_score * 0.25

    # Hedging penalty — excessive uncertainty language
    hedging_penalty = hedging_score * 0.15

    # Lack of specificity penalty — no verifiable details
    # Inverted: low specificity = high penalty
    specificity_penalty = (1.0 - specificity_score) * 0.20

    # AI generation penalty
    ai_penalty = ai_score * 0.15

    # Traditional heuristic penalties
    clickbait_penalty = clickbait * 0.10
    subjectivity_penalty = subjectivity * 0.05
    caps_penalty = min(linguistic.get("caps_ratio", 0) * 3, 1.0) * 0.05
    red_flag_penalty = min(len(red_flags) / 5.0, 1.0) * 0.10

    total_penalty = (
        vague_penalty +
        hedging_penalty +
        specificity_penalty +
        ai_penalty +
        clickbait_penalty +
        subjectivity_penalty +
        caps_penalty +
        red_flag_penalty
    )

    # --- Bonus signals (each increases credibility) ---
    credibility_bonus = credibility_signal_score * 0.15
    specificity_bonus = specificity_score * 0.10

    total_bonus = credibility_bonus + specificity_bonus

    # --- Compute final score ---
    if MODEL_LOADED:
        # Blend: model (40%) + heuristic assessment (60%)
        # The heuristic side starts at 0.5 (neutral) and is adjusted
        heuristic_assessment = 0.5 - total_penalty + total_bonus
        heuristic_assessment = max(0.0, min(1.0, heuristic_assessment))
        credibility = model_score * 0.40 + heuristic_assessment * 0.60
    else:
        # Without model: pure heuristic
        credibility = 0.5 - total_penalty + total_bonus
        credibility = max(0.0, min(1.0, credibility))

    credibility_pct = round(credibility * 100, 1)

    # Clamp to reasonable range
    credibility_pct = max(5.0, min(95.0, credibility_pct))

    # ═══════════════════════════════════════════════════════════════════════
    # LABEL
    # ═══════════════════════════════════════════════════════════════════════
    if credibility_pct >= 70:
        label = "Likely Real"
    elif credibility_pct >= 40:
        label = "Uncertain"
    else:
        label = "Likely Fake"

    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    summary_parts = []
    if credibility_pct >= 70:
        summary_parts.append("This article appears to be credible based on our analysis.")
    elif credibility_pct >= 40:
        summary_parts.append("This article shows mixed credibility signals and should be verified with trusted sources.")
    else:
        summary_parts.append("This article contains multiple indicators of unreliable or fabricated content.")

    if red_flags:
        summary_parts.append(f"We detected {len(red_flags)} warning signal(s).")

    # Add specific insights to summary
    if vague_score >= 0.5:
        summary_parts.append("The article relies heavily on vague, unnamed sources.")
    if hedging_score >= 0.5:
        summary_parts.append("High amount of hedging/uncertainty language reduces verifiability.")
    if specificity_score < 0.15:
        summary_parts.append("The article lacks specific verifiable details (names, quotes, data).")
    if ai_score >= 0.5:
        summary_parts.append("Text patterns suggest possible AI-generated content.")
    if clickbait > 0.5:
        summary_parts.append("The content uses clickbait-style language.")
    if credibility_signal_score >= 0.5:
        summary_parts.append("Article contains credible source attributions.")

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
