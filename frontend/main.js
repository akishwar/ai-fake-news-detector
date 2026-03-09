/* ═══════════════════════════════════════════════════════════════════════════
   TruthLens — Main Application Logic
   Handles API calls, Chart.js visualizations, history, and UI interactions
   ═══════════════════════════════════════════════════════════════════════════ */

const API_URL = 'http://localhost:8000';

// ── Sample articles for demo ───────────────────────────────────────────────
const SAMPLES = {
    real: `New Delhi, March 7 (Reuters) — India's space agency ISRO successfully launched the PSLV-C58 rocket carrying the XPoSat satellite from the Satish Dhawan Space Centre in Sriharikota on Monday at 9:10 AM IST. The mission, India's first dedicated polarimetry observatory, will study X-ray emissions from black holes and neutron stars over the next five years.\n\n"This is a landmark achievement for Indian astrophysics," said ISRO Chairman S. Somanath during the post-launch press briefing. "The satellite has been placed in a 650 km low-Earth orbit with all systems functioning normally."\n\nThe Rs 250-crore mission was developed in collaboration with the Raman Research Institute in Bangalore. Dr. Varun Bhalerao, principal investigator from IIT Bombay, confirmed that initial telemetry data looks "extremely promising." The European Space Agency congratulated ISRO, calling it "a significant contribution to global space research."`,
    fake: `BREAKING!!! You WON'T BELIEVE what they're hiding from us!! Scientists have EXPOSED a massive government COVERUP about vaccines!! According to sources, Big Pharma has been secretly adding mind-control chips to every vaccine since 2020!! Mainstream media WON'T tell you this but MILLIONS of people are waking up!! Doctors hate this one weird trick that proves vaccines are DANGEROUS!! Share before this gets DELETED!! The truth is being SUPPRESSED by corrupt officials who don't want you to know the REAL statistics!! Many experts believe this is the biggest scandal in HISTORY!!`,
};

// ── DOM Elements ───────────────────────────────────────────────────────────
const articleInput = document.getElementById('articleInput');
const charCount = document.getElementById('charCount');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const resultsSection = document.getElementById('results');
const loadingOverlay = document.getElementById('loadingOverlay');
const themeToggle = document.getElementById('themeToggle');

// ── Initialize ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initParticles();
    initNavbar();
    initCharCount();
    initButtons();
    initSampleButtons();
    initFileUpload();
    renderHistory();
});

// ── Theme Toggle ───────────────────────────────────────────────────────────
function initTheme() {
    const savedTheme = localStorage.getItem('truthlens_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('truthlens_theme', next);

        // Re-render charts if results are visible (to update colors)
        if (!resultsSection.classList.contains('hidden')) {
            updateChartColors(next);
        }
    });
}

function updateChartColors(theme) {
    // Update keywords chart tick colors
    if (keywordsChartInstance) {
        const tickColor = theme === 'light' ? '#8a8aaa' : '#686890';
        const labelColor = theme === 'light' ? '#4a4a6a' : '#a0a0c0';
        const gridColor = theme === 'light' ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)';
        keywordsChartInstance.options.scales.x.ticks.color = tickColor;
        keywordsChartInstance.options.scales.y.ticks.color = labelColor;
        keywordsChartInstance.options.scales.x.grid.color = gridColor;
        keywordsChartInstance.update();
    }

    // Update gauge background
    if (gaugeChartInstance) {
        const bgColor = theme === 'light' ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)';
        gaugeChartInstance.data.datasets[0].backgroundColor[1] = bgColor;
        gaugeChartInstance.update();
    }
}

// ── Background Particles ───────────────────────────────────────────────────
function initParticles() {
    const container = document.getElementById('bgParticles');
    const colors = ['#818cf8', '#60a5fa', '#22d3ee', '#34d399'];

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        const size = Math.random() * 6 + 2;
        const color = colors[Math.floor(Math.random() * colors.length)];
        particle.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${Math.random() * 100}%;
            background: ${color};
            animation-duration: ${Math.random() * 15 + 10}s;
            animation-delay: ${Math.random() * 10}s;
        `;
        container.appendChild(particle);
    }
}

// ── Navbar Scroll Effect ───────────────────────────────────────────────────
function initNavbar() {
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 50);
    });
}

// ── Character Count ────────────────────────────────────────────────────────
function initCharCount() {
    articleInput.addEventListener('input', () => {
        const len = articleInput.value.length;
        charCount.textContent = `${len.toLocaleString()} characters`;
    });
}

// ── Button Handlers ────────────────────────────────────────────────────────
function initButtons() {
    analyzeBtn.addEventListener('click', handleAnalyze);
    clearBtn.addEventListener('click', () => {
        articleInput.value = '';
        charCount.textContent = '0 characters';
        resultsSection.classList.add('hidden');
    });
}

// ── Sample Buttons ─────────────────────────────────────────────────────────
function initSampleButtons() {
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const sample = btn.getAttribute('data-sample');
            articleInput.value = SAMPLES[sample];
            articleInput.dispatchEvent(new Event('input'));
            articleInput.focus();
        });
    });
}

// ── File Upload ────────────────────────────────────────────────────────────
function initFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadContent = document.getElementById('uploadContent');
    const uploadProgress = document.getElementById('uploadProgress');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    async function handleFile(file) {
        const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showToast('Unsupported file type. Please upload a PDF, JPG, or PNG.', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        uploadContent.classList.add('hidden');
        uploadProgress.classList.remove('hidden');

        try {
            const response = await fetch(`${API_URL}/api/extract-text`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();

            // Populate textarea with extracted text
            articleInput.value = data.text;
            articleInput.dispatchEvent(new Event('input'));

            showToast(`Successfully extracted text from ${file.name}`, 'success');

            // Auto trigger analysis
            setTimeout(() => handleAnalyze(), 500);

        } catch (error) {
            console.error('File extraction failed:', error);
            showToast(error.message, 'error');
        } finally {
            uploadProgress.classList.add('hidden');
            uploadContent.classList.remove('hidden');
            fileInput.value = ''; // Reset input
        }
    }
}

// ── Main Analyze Handler ───────────────────────────────────────────────────
async function handleAnalyze() {
    const text = articleInput.value.trim();

    if (text.length < 10) {
        showToast('Please enter at least 10 characters for analysis.', 'warning');
        return;
    }

    // Show loading
    showLoading(true);
    analyzeBtn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
        saveToHistory(text, data);

    } catch (error) {
        console.error('Analysis failed:', error);
        showToast(`Analysis failed: ${error.message}. Make sure the backend is running.`, 'error');
    } finally {
        showLoading(false);
        analyzeBtn.disabled = false;
    }
}

// ── Loading Animation ──────────────────────────────────────────────────────
function showLoading(show) {
    loadingOverlay.classList.toggle('hidden', !show);

    if (show) {
        const steps = ['step1', 'step2', 'step3'];
        steps.forEach(s => {
            document.getElementById(s).classList.remove('active', 'done');
        });
        document.getElementById('step1').classList.add('active');

        setTimeout(() => {
            document.getElementById('step1').classList.replace('active', 'done');
            document.getElementById('step2').classList.add('active');
        }, 800);

        setTimeout(() => {
            document.getElementById('step2').classList.replace('active', 'done');
            document.getElementById('step3').classList.add('active');
        }, 1600);
    }
}

// ── Display Results ────────────────────────────────────────────────────────
function displayResults(data) {
    resultsSection.classList.remove('hidden');

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Summary
    document.getElementById('resultsSummary').textContent = data.summary;

    // Credibility score gauge
    renderGauge(data.credibility_score);

    // Score label
    const scoreLabel = document.getElementById('scoreLabel');
    scoreLabel.textContent = data.label;
    scoreLabel.className = 'score-label';
    if (data.credibility_score >= 70) scoreLabel.classList.add('real');
    else if (data.credibility_score >= 40) scoreLabel.classList.add('uncertain');
    else scoreLabel.classList.add('fake');

    // Gauge value color
    const gaugeValue = document.getElementById('gaugeValue');
    gaugeValue.textContent = Math.round(data.credibility_score);
    if (data.credibility_score >= 70) gaugeValue.style.color = '#34d399';
    else if (data.credibility_score >= 40) gaugeValue.style.color = '#fbbf24';
    else gaugeValue.style.color = '#f87171';

    // Score card border glow
    const scoreCard = document.getElementById('scoreCard');
    if (data.credibility_score >= 70) scoreCard.style.borderColor = 'rgba(52,211,153,0.3)';
    else if (data.credibility_score >= 40) scoreCard.style.borderColor = 'rgba(251,191,36,0.3)';
    else scoreCard.style.borderColor = 'rgba(248,113,113,0.3)';

    // Confidence bar
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceValue = document.getElementById('confidenceValue');
    confidenceBar.style.width = `${data.confidence * 100}%`;
    confidenceValue.textContent = `${Math.round(data.confidence * 100)}%`;

    // Content signals
    renderSignals(data.insights);

    // Keywords chart
    renderKeywordsChart(data.insights.keywords);

    // Red flags
    renderFlags(data.insights.red_flags);

    // Entities
    renderEntities(data.insights.entities);

    // Linguistic stats
    renderStats(data.insights.linguistic_features);
}

// ── Gauge Chart (Chart.js Doughnut) ────────────────────────────────────────
let gaugeChartInstance = null;

function renderGauge(score) {
    const ctx = document.getElementById('gaugeChart').getContext('2d');

    if (gaugeChartInstance) {
        gaugeChartInstance.destroy();
    }

    let color;
    if (score >= 70) color = '#34d399';
    else if (score >= 40) color = '#fbbf24';
    else color = '#f87171';

    gaugeChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [color, 'rgba(255,255,255,0.04)'],
                borderWidth: 0,
                circumference: 270,
                rotation: 225,
            }]
        },
        options: {
            responsive: false,
            cutout: '80%',
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            animation: {
                animateRotate: true,
                duration: 1500,
                easing: 'easeOutCubic',
            },
        },
    });
}

// ── Content Signal Bars ────────────────────────────────────────────────────
function renderSignals(insights) {
    // Clickbait
    const clickbaitPct = Math.round(insights.clickbait_score * 100);
    document.getElementById('clickbaitValue').textContent = `${clickbaitPct}%`;
    document.getElementById('clickbaitBar').style.width = `${clickbaitPct}%`;

    // Subjectivity
    const subPct = Math.round(insights.subjectivity_score * 100);
    document.getElementById('subjectivityValue').textContent = `${subPct}%`;
    document.getElementById('subjectivityBar').style.width = `${subPct}%`;

    // Sentiment
    document.getElementById('sentimentValue').textContent = `${insights.sentiment} (${Math.round(insights.sentiment_score * 100)}%)`;
    const sentimentMap = { positive: 80, neutral: 50, negative: 20 };
    document.getElementById('sentimentBar').style.width = `${sentimentMap[insights.sentiment] || 50}%`;
}

// ── Keywords Bar Chart ─────────────────────────────────────────────────────
let keywordsChartInstance = null;

function renderKeywordsChart(keywords) {
    const ctx = document.getElementById('keywordsChart').getContext('2d');

    if (keywordsChartInstance) {
        keywordsChartInstance.destroy();
    }

    if (!keywords || keywords.length === 0) return;

    const labels = keywords.map(k => k.word);
    const weights = keywords.map(k => k.weight);

    const colors = [
        'rgba(129,140,248,0.7)', 'rgba(96,165,250,0.7)', 'rgba(34,211,238,0.7)',
        'rgba(52,211,153,0.7)', 'rgba(251,191,36,0.7)', 'rgba(251,146,60,0.7)',
        'rgba(244,114,182,0.7)', 'rgba(248,113,113,0.7)',
    ];

    keywordsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Weight',
                data: weights,
                backgroundColor: colors.slice(0, keywords.length),
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17,17,40,0.95)',
                    titleColor: '#f0f0ff',
                    bodyColor: '#a0a0c0',
                    borderColor: 'rgba(129,140,248,0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 10,
                },
            },
            scales: {
                x: {
                    ticks: { color: '#686890', font: { size: 11 } },
                    grid: { color: 'rgba(255,255,255,0.04)' },
                },
                y: {
                    ticks: { color: '#a0a0c0', font: { size: 12, weight: 500 } },
                    grid: { display: false },
                },
            },
            animation: { duration: 1000, easing: 'easeOutCubic' },
        },
    });
}

// ── Red Flags ──────────────────────────────────────────────────────────────
function renderFlags(flags) {
    const container = document.getElementById('flagsList');
    if (!flags || flags.length === 0) {
        container.innerHTML = '<div class="no-flags">✅ No warning signals detected — good sign!</div>';
        return;
    }

    container.innerHTML = flags.map(flag =>
        `<div class="flag-item">
            <span class="flag-icon">⚠️</span>
            <span>${escapeHtml(flag)}</span>
        </div>`
    ).join('');
}

// ── Named Entities ─────────────────────────────────────────────────────────
function renderEntities(entities) {
    const container = document.getElementById('entitiesList');
    if (!entities || entities.length === 0) {
        container.innerHTML = '<span class="entity-tag" style="opacity:0.5">No entities detected</span>';
        return;
    }

    container.innerHTML = entities.map(e =>
        `<span class="entity-tag">${escapeHtml(e)}</span>`
    ).join('');
}

// ── Linguistic Stats ───────────────────────────────────────────────────────
function renderStats(features) {
    if (!features) return;
    document.getElementById('wordCount').textContent = features.word_count || '—';
    document.getElementById('sentenceCount').textContent = features.sentence_count || '—';
    document.getElementById('avgSentenceLen').textContent = features.avg_sentence_length || '—';
    document.getElementById('vocabRichness').textContent =
        features.vocabulary_richness ? `${Math.round(features.vocabulary_richness * 100)}%` : '—';
}

// ── History ────────────────────────────────────────────────────────────────
function getHistory() {
    try {
        return JSON.parse(localStorage.getItem('truthlens_history') || '[]');
    } catch { return []; }
}

function saveToHistory(text, data) {
    const history = getHistory();
    history.unshift({
        text: text.substring(0, 150),
        score: data.credibility_score,
        label: data.label,
        timestamp: new Date().toISOString(),
    });
    // Keep last 20
    localStorage.setItem('truthlens_history', JSON.stringify(history.slice(0, 20)));
    renderHistory();
}

function renderHistory() {
    const container = document.getElementById('historyContainer');
    const history = getHistory();

    if (history.length === 0) {
        container.innerHTML = '<div class="history-empty"><p>No analyses yet. Start by analyzing an article above!</p></div>';
        return;
    }

    container.innerHTML = history.map(item => {
        let scoreClass, labelClass;
        if (item.score >= 70) { scoreClass = 'high'; labelClass = 'real'; }
        else if (item.score >= 40) { scoreClass = 'mid'; labelClass = 'uncertain'; }
        else { scoreClass = 'low'; labelClass = 'fake'; }

        const date = new Date(item.timestamp);
        const timeStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return `
            <div class="history-item">
                <div class="history-score ${scoreClass}">${Math.round(item.score)}</div>
                <div class="history-info">
                    <div class="history-text">${escapeHtml(item.text)}</div>
                    <div class="history-meta">${timeStr}</div>
                </div>
                <span class="history-label ${labelClass}">${item.label}</span>
            </div>
        `;
    }).join('');
}

// ── Toast Notification ─────────────────────────────────────────────────────
function showToast(message, type = 'info') {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        padding: 16px 24px;
        background: ${type === 'error' ? 'rgba(248,113,113,0.15)' : type === 'warning' ? 'rgba(251,191,36,0.15)' : 'rgba(129,140,248,0.15)'};
        border: 1px solid ${type === 'error' ? 'rgba(248,113,113,0.3)' : type === 'warning' ? 'rgba(251,191,36,0.3)' : 'rgba(129,140,248,0.3)'};
        border-radius: 12px;
        color: ${type === 'error' ? '#f87171' : type === 'warning' ? '#fbbf24' : '#818cf8'};
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        max-width: 400px;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        animation: fadeInUp 0.3s ease-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ── Utility ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
