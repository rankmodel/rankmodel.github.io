import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv('HF_TOKEN')
HF_API_BASE = 'https://huggingface.co/api'
CACHE_DB_PATH = 'data/modelrank.db'
CACHE_TTL_METADATA = 86400  # 24h in seconds
CACHE_TTL_EVALS = 21600     # 6h in seconds
MAX_RETRIES = 3
RETRY_DELAY = 2.0
LOG_LEVEL = 'INFO'
BADGE_OUTPUT_DIR = 'brand/templates/'
API_HOST = '0.0.0.0'
API_PORT = 8000
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '*').split(',')]
TOP_MODELS_LIMIT = 1000

SCORING_WEIGHTS = {
    "benchmarks": 0.40,
    "efficiency": 0.20,
    "community": 0.20,
    "recency": 0.10,
    "reproducibility": 0.10,
}

BENCHMARK_WEIGHTS = {
    "MMLU-Pro": 0.25,
    "GPQA": 0.20,
    "HLE": 0.20,
    "GSM8K": 0.20,
    "HumanEval": 0.15,
}

# Tier thresholds: numeric score -> tier letter (score >= threshold)
TIERS = {
    90: "S",   # 90-100
    80: "A",   # 80-89
    70: "B",   # 70-79
    60: "C",   # 60-69
    0:  "D",   # <60
}

DIMENSION_COLORS = {
    'benchmarks': '#6366f1',
    'efficiency': '#22c55e',
    'community': '#f59e0b',
    'recency': '#06b6d4',
    'reproducibility': '#ec4899'
}

TIER_COLORS = {
    'S': '#a855f7',
    'A': '#3b82f6',
    'B': '#22c55e',
    'C': '#eab308',
    'D': '#ef4444'
}

RANK_COLORS = {
    'gold': '#ffd700',
    'silver': '#c0c0c0',
    'bronze': '#cd7f32',
    'default': '#ffffff'
}

ACHIEVEMENT_TYPES = [
    {"id": "trending_top10",      "name": "Trending Top 10",      "icon": "🔥", "color": "#ef4444", "description": "In the top 10 trending models on HuggingFace"},
    {"id": "efficiency_king",      "name": "Efficiency King",       "icon": "⚡", "color": "#22c55e", "description": "Exceptional performance per parameter"},
    {"id": "community_favorite",   "name": "Community Favorite",   "icon": "❤️", "color": "#ec4899", "description": "Highly popular with 10k+ downloads and likes"},
    {"id": "benchmark_champion",   "name": "Benchmark Champion",   "icon": "🏆", "color": "#fbbf24", "description": "Top-tier benchmark performance across all evals"},
    {"id": "abliterated",          "name": "Abliterated",          "icon": "🔓", "color": "#a855f7", "description": "Uncensored / abliterated model variant"},
    {"id": "quantized_ready",      "name": "Quantized Ready",      "icon": "📦", "color": "#3b82f6", "description": "Available in GGUF / AWQ / GPTQ formats"},
    {"id": "top_1",                "name": "#1 Global",            "icon": "👑", "color": "#fbbf24", "description": "The #1 ranked model globally"},
    {"id": "top_3",                "name": "Top 3 Global",         "icon": "🥈", "color": "#94a3b8", "description": "Top 3 ranked model globally"},
    {"id": "top_10",               "name": "Top 10 Global",        "icon": "🏅", "color": "#cd7c3a", "description": "Top 10 ranked model globally"},
]

def get_settings():
    return {
        k: v for k, v in globals().items() if not k.startswith('__') and not callable(v) and k not in ('os', 'load_dotenv')
    }
