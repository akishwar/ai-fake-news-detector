"""Text preprocessing utilities for the NLP pipeline.

Enhanced with deeper analysis for detecting well-written fake news,
AI-generated content, vague attribution, hedging language, and
lack of verifiable details.
"""

import re
import string
import math
from collections import Counter


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL DICTIONARIES
# ═══════════════════════════════════════════════════════════════════════════

# Common clickbait trigger phrases
CLICKBAIT_PHRASES = [
    "you won't believe", "shocking", "breaking", "urgent", "must see",
    "what happens next", "jaw-dropping", "mind-blowing", "unbelievable",
    "secret", "they don't want you to know", "exposed", "bombshell",
    "gone wrong", "watch before deleted", "this changes everything",
    "doctors hate", "one weird trick", "is dead", "destroyed",
]

# ── Vague attribution phrases (key indicator of fabricated news) ─────────
VAGUE_ATTRIBUTION = [
    r"according to (?:some |anonymous |unnamed )?sources?",
    r"(?:sources?|officials?|people|experts?) (?:say|said|believe|suggest|indicate|claim|familiar with)",
    r"reportedly",
    r"it is (?:being )?(?:reported|said|believed|suggested|expected|rumored)",
    r"(?:many|some|several|various) (?:experts?|officials?|analysts?|people|observers?) (?:say|said|believe|think|suggest|note|point out)",
    r"people (?:are )?saying",
    r"(?:sources?|those|people|officials?) (?:close to|familiar with|with knowledge of|briefed on)",
    r"(?:an?|the) (?:official|source|person|insider) (?:who|that) (?:spoke|asked|declined)",
    r"(?:is|are|was|were) (?:said to|believed to|expected to|reported to|thought to|rumored to)",
    r"(?:unconfirmed|unverified) reports? (?:suggest|indicate|say|claim)",
]

# ── Hedging / uncertainty language ──────────────────────────────────────
HEDGING_PHRASES = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bwould\b",
    r"\bpossibly\b", r"\bpotentially\b", r"\bperhaps\b", r"\blikely\b",
    r"\bexpected to\b", r"\banticipated\b", r"\bplanned\b",
    r"\bif successful\b", r"\bremains to be seen\b",
    r"\bnot yet (?:announced|confirmed|decided|determined|clear|known)\b",
    r"\bhave not (?:yet )?(?:announced|confirmed|released|disclosed)\b",
    r"\bin the (?:coming|next|near|following) (?:weeks?|months?|days?|years?)\b",
    r"\bwithin the next\b",
    r"\bcould (?:potentially|eventually|later)\b",
    r"\bis (?:considering|exploring|evaluating|planning|preparing)\b",
    r"\bset to\b", r"\baiming to\b", r"\bhoping to\b",
]

# ── Red flag patterns ──────────────────────────────────────────────────
RED_FLAG_PATTERNS = [
    r"according to (?:some |anonymous )?sources",
    r"people (?:are )?saying",
    r"it is (?:being )?reported",
    r"many (?:experts|people|scientists) (?:believe|say|think)",
    r"exposed|coverup|cover-up|conspiracy",
    r"mainstream media won'?t tell you",
    r"wake up|sheeple",
    r"big pharma|big tech",
]

# ── Emotional / sensational words ──────────────────────────────────────
EMOTIONAL_WORDS = [
    "outrageous", "horrifying", "terrifying", "devastating", "incredible",
    "unacceptable", "disgusting", "catastrophic", "nightmare", "miracle",
    "evil", "corrupt", "criminal", "traitor", "hero", "villain",
    "explosive", "massive", "enormous", "tremendous",
]

# ── Words that signal proper journalism / credibility ──────────────────
CREDIBILITY_SIGNALS = [
    r"according to (?:the |a )?(?:\w+ )?(?:university|institute|journal|organization|ministry|department|bureau|agency|commission)",
    r"(?:published|peer-reviewed|peer reviewed) (?:in|by|study|research|paper|report)",
    r"(?:dr\.|prof\.|professor|minister|secretary|director|chief|chairman|spokesperson) [A-Z][a-z]+ [A-Z][a-z]+",
    r"\b(?:doi|isbn|issn|arxiv)\b",
    r"press (?:release|conference|briefing|statement)",
    r"official (?:statement|announcement|report|data|figures|press)",
    r"confirmed (?:by|to|that|in)",
    r"(?:the|a) (?:study|survey|report|investigation|analysis) (?:by|from|published|conducted|found|showed|revealed)",
    r"(?:reuters|associated press|ap news|bbc|cnn|al jazeera|the guardian|new york times|washington post|pti|ani|ians)",
    r"(?:quoted|cited|referenced|attributed to) (?:in|by)",
]

# ── AI-generated text patterns ─────────────────────────────────────────
AI_GENERATION_PHRASES = [
    r"(?:this|the) (?:move|initiative|step|decision|development) (?:is|was|has been|comes) (?:aimed|designed|intended|expected|seen as|part of)",
    r"(?:aims?|aim(?:ed|ing|s)?) to (?:reduce|improve|enhance|increase|streamline|modernize|boost|transform)",
    r"(?:if successful|once implemented|when completed|upon completion)",
    r"(?:remain(?:s|ed)?) to be seen",
    r"(?:the|this) (?:project|program|initiative|scheme|plan|system|technology) (?:is|was|will be) (?:designed|aimed|expected|intended|set) to",
    r"(?:could|would|may) (?:later|eventually|subsequently|further|also) be (?:expanded|extended|rolled out|scaled|implemented)",
    r"(?:is|was|are|were) (?:being )?(?:hailed|touted|described|seen|viewed|regarded) as",
    r"no (?:official|specific|definite|concrete|exact) (?:date|timeline|deadline|schedule|plan|statement|comment|response)",
]


# ═══════════════════════════════════════════════════════════════════════════
# CORE PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Clean and normalize input text."""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_clickbait_score(text: str) -> float:
    """Compute a clickbait probability score based on trigger phrases."""
    text_lower = text.lower()
    matches = sum(1 for phrase in CLICKBAIT_PHRASES if phrase in text_lower)
    return min(matches / 3.0, 1.0)


def compute_subjectivity_score(text: str) -> float:
    """Estimate subjectivity based on opinion indicators."""
    opinion_words = [
        "i think", "i believe", "in my opinion", "obviously", "clearly",
        "everyone knows", "without doubt", "undoubtedly", "surely",
        "of course", "it seems", "apparently", "allegedly",
    ]
    text_lower = text.lower()
    matches = sum(1 for w in opinion_words if w in text_lower)
    return min(matches / 4.0, 1.0)


def compute_vague_attribution_score(text: str) -> tuple[float, list[str]]:
    """
    Detect vague/unnamed sourcing — a key indicator of fabricated news.
    Well-written fake news often uses phrases like "reportedly", "officials say",
    "sources familiar with" without naming specific people or organizations.
    Returns (score 0-1, list of matched phrases).
    """
    text_lower = text.lower()
    matched = []

    for pattern in VAGUE_ATTRIBUTION:
        found = re.findall(pattern, text_lower)
        if found:
            matched.extend(found)

    # Also check for attribution WITHOUT a named source
    # e.g., "Officials say" vs "Dr. Maria Chen, lead researcher, says"
    generic_attributions = re.findall(
        r'\b(?:officials?|sources?|experts?|analysts?|observers?|insiders?|authorities|people)\b'
        r'(?:\s+\w+){0,3}\s+'
        r'(?:say|said|believe|suggest|indicate|claim|note|point out|add|explain)',
        text_lower
    )
    matched.extend(generic_attributions)

    # Normalize: 2+ vague attributions is highly suspicious
    unique_matches = list(set(matched))
    score = min(len(unique_matches) / 2.0, 1.0)
    return score, unique_matches


def compute_hedging_score(text: str) -> tuple[float, int]:
    """
    Detect excessive hedging/uncertainty language.
    Legitimate news tends to report facts; fake news uses hedging to avoid
    making falsifiable claims.
    Returns (score 0-1, count of hedging instances).
    """
    text_lower = text.lower()
    count = 0
    for pattern in HEDGING_PHRASES:
        count += len(re.findall(pattern, text_lower))

    # Normalize by text length (per 100 words)
    word_count = len(text.split())
    if word_count == 0:
        return 0.0, 0

    hedging_density = count / (word_count / 100.0)
    # 3+ hedging phrases per 100 words is suspicious
    score = min(hedging_density / 3.0, 1.0)
    return score, count


def compute_specificity_score(text: str) -> tuple[float, dict]:
    """
    Measure how specific and verifiable the article is.
    Real news contains specific names, dates, numbers, locations, and quotes.
    Fake news often avoids specific falsifiable details.
    Returns (score 0-1 where LOWER = more suspicious, detail_counts).
    """
    # Count specific numbers/statistics
    numbers = re.findall(r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|\s*crore|\s*lakh|\s*million|\s*billion|\s*thousand)?\b', text)
    number_count = len(numbers)

    # Count direct quotes (text within quotation marks)
    quotes = re.findall(r'["""]([^"""]{10,})["""]', text)
    quote_count = len(quotes)

    # Count named people (First Last pattern with title)
    named_people = re.findall(
        r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Minister|Commissioner|Director|Chief|Secretary|Chairman|Spokesperson|CEO|CTO|CFO)\s+'
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}',
        text
    )
    # Also try simple "Name Name said" pattern
    named_quotes = re.findall(
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:said|told|stated|explained|noted|added|confirmed|announced|remarked)',
        text
    )
    people_count = len(set(named_people)) + len(set(named_quotes))

    # Count specific dates
    dates = re.findall(
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s+\d{4})?\b'
        r'|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        r'|\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        text
    )
    date_count = len(dates)

    # Count specific organization names (capitalized multi-word names)
    org_patterns = re.findall(
        r'\b(?:the\s+)?(?:[A-Z][a-z]+\s+){1,4}(?:Corporation|Company|Ltd|Inc|Organization|Commission|Authority|Department|Ministry|Bureau|Agency|Board|Council|Committee|Foundation|Institute|University|College|Hospital|Bank|Railway|Airlines?|Association)\b',
        text
    )
    org_count = len(set(org_patterns))

    details = {
        "numbers": number_count,
        "quotes": quote_count,
        "named_people": people_count,
        "dates": date_count,
        "organizations": org_count,
    }

    # Score: more specific details = higher specificity
    word_count = len(text.split())
    if word_count == 0:
        return 0.0, details

    # Weight different types of specificity
    specificity_points = (
        min(number_count, 5) * 0.15 +
        min(quote_count, 3) * 0.25 +
        min(people_count, 3) * 0.25 +
        min(date_count, 3) * 0.15 +
        min(org_count, 3) * 0.20
    )

    # Normalize to 0-1 (max points ≈ 3.0)
    score = min(specificity_points / 2.0, 1.0)
    return score, details


def compute_ai_generation_score(text: str) -> tuple[float, list[str]]:
    """
    Detect patterns common in AI-generated news articles.
    AI-generated text tends to have:
    - Formulaic sentence structures
    - Excessive hedging without claiming facts
    - Suspiciously uniform sentence lengths
    - Generic "filler" phrases
    - Smooth, overly balanced prose
    Returns (score 0-1, list of matched patterns).
    """
    text_lower = text.lower()
    matched = []

    # Check AI-typical phrases
    for pattern in AI_GENERATION_PHRASES:
        found = re.findall(pattern, text_lower)
        if found:
            matched.extend(found)

    # Sentence length uniformity (AI tends to produce suspiciously consistent sentence lengths)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip() and len(s.strip()) > 10]
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        if mean_len > 0:
            variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            coeff_variation = std_dev / mean_len
            # Very low variation (< 0.3) is suspicious — AI writes very uniform sentences
            if coeff_variation < 0.25:
                matched.append(f"suspiciously uniform sentence lengths (CV={coeff_variation:.2f})")

    # Check for lack of contractions (AI tends to write formally)
    contraction_count = len(re.findall(r"\b(?:don't|doesn't|won't|can't|isn't|aren't|wasn't|weren't|couldn't|wouldn't|shouldn't|hasn't|haven't|hadn't|didn't|it's|that's|there's|here's|what's|who's|he's|she's|we're|they're|you're|I'm|I've|I'll|I'd)\b", text, re.IGNORECASE))
    words = text.split()
    word_count = len(words)
    if word_count > 50 and contraction_count == 0:
        matched.append("no contractions used (formal/AI-like writing)")

    # Check for smooth paragraph transitions (another AI tell)
    transition_phrases = re.findall(
        r'(?:additionally|furthermore|moreover|in addition|similarly|likewise|'
        r'consequently|as a result|therefore|thus|hence|meanwhile|'
        r'on the other hand|however|nevertheless|nonetheless|'
        r'in conclusion|overall|in summary|to summarize)',
        text_lower
    )
    if len(transition_phrases) >= 3:
        matched.append(f"excessive transition phrases ({len(transition_phrases)} found)")

    # Normalize
    score = min(len(matched) / 3.0, 1.0)
    return score, matched


def compute_credibility_signals_score(text: str) -> tuple[float, list[str]]:
    """
    Check for signals of legitimate, credible journalism.
    Returns (score 0-1 where HIGHER = more credible, list of signals found).
    """
    text_lower = text.lower()
    found_signals = []

    for pattern in CREDIBILITY_SIGNALS:
        matches = re.findall(pattern, text_lower)
        if matches:
            found_signals.extend(matches)

    # Check for wire service formatting
    wire_dateline = re.search(r'^[A-Z][A-Z\s]+,\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text)
    if wire_dateline:
        found_signals.append("wire service dateline format")

    # Check for proper quoted attribution: "quote," said Name
    proper_quotes = re.findall(r'["""][^"""]+["""]\s*(?:,\s*)?(?:said|told|stated)\s+[A-Z][a-z]+', text)
    if proper_quotes:
        found_signals.extend(proper_quotes[:3])

    unique_signals = list(set(found_signals))
    score = min(len(unique_signals) / 3.0, 1.0)
    return score, unique_signals


def detect_red_flags(text: str) -> list[str]:
    """Detect red flag patterns in the text — enhanced version."""
    text_lower = text.lower()
    flags = []

    # Classic red flag patterns
    for pattern in RED_FLAG_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            flags.append(f"Vague sourcing: '{match.group()}'")

    # Excessive caps
    words = text.split()
    caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
    if caps_ratio > 0.15:
        flags.append("Excessive use of ALL CAPS")

    # Excessive punctuation
    exclamation_count = text.count('!')
    question_count = text.count('?')
    if exclamation_count > 3:
        flags.append(f"Excessive exclamation marks ({exclamation_count} found)")
    if question_count > 5:
        flags.append(f"Excessive question marks ({question_count} found)")

    # Emotional language density
    text_lower_words = text_lower.split()
    emotional_count = sum(1 for w in text_lower_words if w.strip(string.punctuation) in EMOTIONAL_WORDS)
    if emotional_count >= 3:
        flags.append(f"High emotional language density ({emotional_count} emotional words)")

    # Missing attribution for claims
    sentences = re.split(r'[.!?]', text)
    claim_sentences = [s for s in sentences if any(w in s.lower() for w in ["studies show", "research proves", "data shows", "statistics"])]
    for s in claim_sentences:
        if not any(w in s.lower() for w in ["university", "journal", "published", "according to", "et al"]):
            flags.append("Claims citing studies without specific attribution")
            break

    # ── NEW: Vague attribution flags ──
    vague_score, vague_matches = compute_vague_attribution_score(text)
    if vague_score >= 0.5:
        flags.append(f"Heavy reliance on vague/unnamed sources ({len(vague_matches)} instances)")
    elif vague_matches:
        for m in vague_matches[:2]:
            flags.append(f"Vague attribution: '{m.strip()}'")

    # ── NEW: Hedging flags ──
    hedging_score, hedging_count = compute_hedging_score(text)
    if hedging_score >= 0.5:
        flags.append(f"Excessive hedging/uncertainty language ({hedging_count} instances)")
    elif hedging_count >= 3:
        flags.append(f"Notable hedging language ({hedging_count} instances)")

    # ── NEW: Lack of specificity flags ──
    spec_score, spec_details = compute_specificity_score(text)
    if spec_score < 0.15:
        missing_items = []
        if spec_details["quotes"] == 0:
            missing_items.append("direct quotes")
        if spec_details["named_people"] == 0:
            missing_items.append("named individuals")
        if spec_details["numbers"] <= 1:
            missing_items.append("specific data/statistics")
        if missing_items:
            flags.append(f"Missing verifiable details: no {', '.join(missing_items)}")

    # ── NEW: AI generation flags ──
    ai_score, ai_matches = compute_ai_generation_score(text)
    if ai_score >= 0.5:
        flags.append("Text exhibits patterns typical of AI-generated content")
    if ai_matches:
        for m in ai_matches[:2]:
            if len(m) < 80:
                flags.append(f"AI-typical pattern: '{m}'")

    # ── NEW: No verifiable source ──
    cred_score, _ = compute_credibility_signals_score(text)
    if cred_score == 0:
        flags.append("No identifiable credible source, publication, or official attribution")

    return flags


def extract_keywords(text: str, top_n: int = 8) -> list[dict]:
    """Extract top keywords with weights from text using TF analysis."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "because", "but",
        "and", "or", "if", "while", "that", "this", "these", "those",
        "it", "its", "he", "she", "they", "them", "his", "her", "their",
        "what", "which", "who", "whom", "we", "you", "i", "me", "my",
        "your", "our", "said", "also", "about", "up", "one", "two",
        "new", "even", "get", "got", "still", "well", "way", "many",
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stop_words]
    counts = Counter(filtered)

    total = sum(counts.values()) or 1
    top_words = counts.most_common(top_n)
    return [{"word": word, "weight": round(count / total, 3)} for word, count in top_words]


def compute_linguistic_features(text: str) -> dict:
    """Compute linguistic features for analysis."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()

    avg_sentence_length = len(words) / max(len(sentences), 1)
    unique_words = len(set(w.lower().strip(string.punctuation) for w in words))
    vocabulary_richness = unique_words / max(len(words), 1)

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sentence_length, 1),
        "vocabulary_richness": round(vocabulary_richness, 3),
        "has_urls": bool(re.search(r'https?://\S+', text)),
        "caps_ratio": round(sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1), 3),
    }
