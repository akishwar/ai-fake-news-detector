# TruthLens — AI-Based Fake News Detection & Media Authenticity Platform

> **Problem Statement ID:** 31002 · **Category:** Software · **Theme:** Media / AI

## 🛡️ Overview

TruthLens is an AI-powered platform that analyzes news articles to detect misinformation using Natural Language Processing (NLP), Machine Learning, and Data Visualization.

## 🚀 Features

- **AI Text Classification** — Uses a pre-trained RoBERTa model fine-tuned for fake news detection
- **Multi-Signal Analysis** — Combines ML predictions with linguistic heuristics (clickbait, subjectivity, red flags)
- **Rich Visualizations** — Credibility gauge, keyword charts, sentiment meters, and warning signals
- **Analysis History** — All past analyses saved locally for reference
- **Modern UI** — Stunning dark theme with glassmorphism, animations, and responsive design

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS + Chart.js)  →  REST API  →  Backend (Python FastAPI)
                                                        ↓
                                                   NLP Pipeline
                                                   (HuggingFace Transformers)
```

## 📦 Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The API server starts at `http://localhost:8000`.

### Frontend
```bash
# From the project root
npm run dev
```
The frontend will be available at `http://localhost:5173`.

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/health` | Health check |
| POST   | `/api/analyze` | Analyze article text |

### Example Request
```json
POST /api/analyze
{
  "text": "Your news article text here..."
}
```

### Example Response
```json
{
  "credibility_score": 73.2,
  "label": "Likely Real",
  "confidence": 0.89,
  "summary": "This article appears to be credible...",
  "insights": {
    "sentiment": "neutral",
    "clickbait_score": 0.1,
    "subjectivity_score": 0.0,
    "entities": ["WHO", "CDC"],
    "keywords": [{"word": "study", "weight": 0.08}],
    "red_flags": [],
    "linguistic_features": { ... }
  }
}
```

## 🛠️ Tech Stack

- **Frontend:** Vanilla HTML/CSS/JS, Chart.js
- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **AI/NLP:** Hugging Face Transformers (RoBERTa)
- **Styling:** Modern dark theme, glassmorphism, CSS animations
