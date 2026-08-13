import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from config.settings import API_HOST, API_PORT, ALLOWED_ORIGINS
from data.cache import ModelCache
from data.fetcher import HFDataFetcher
from scoring.engine import compute_composite_score, batch_score_models, get_achievements, compare_models_elo
from badges.generator import BadgeGenerator, generate_badge
from data.models import ModelScore, LeaderboardEntry
from contextlib import asynccontextmanager
from api.premium import router as premium_router

# Global variables for instances
cache = None
fetcher = None
badge_generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache, fetcher, badge_generator
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting up ModelRank API...")
    cache = ModelCache()
    fetcher = HFDataFetcher()
    badge_generator = BadgeGenerator()
    logging.info("ModelCache, HFDataFetcher, and BadgeGenerator initialized.")
    yield
    logging.info("Shutting down ModelRank API...")

app = FastAPI(
    title='ModelRank API',
    description='Rate and rank HuggingFace models with composite scoring',
    version='1.0.0',
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(premium_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "details": str(exc)},
    )

class BatchScoreRequest(BaseModel):
    model_ids: List[str]

@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')

@app.get("/health")
async def health_check():
    # Attempt to get cache size if implemented, otherwise return 0 or placeholder
    try:
        cache_size = cache.get_size() if hasattr(cache, 'get_size') else "unknown"
    except Exception:
        cache_size = "error"
    return {
        "status": "ok",
        "version": app.version,
        "cache_size": cache_size,
        "leaderboard_stats": {
            "total_models": cache_size,
            "tier_distribution": {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0},
            "last_seeded": None
        }
    }

@app.get("/meta")
async def get_meta():
    """Returns leaderboard metadata: version, stats, tier distribution."""
    try:
        cache_size = cache.get_size() if hasattr(cache, 'get_size') else "unknown"
    except Exception:
        cache_size = "error"
    return {
        'version': '2.0.0',
        'total_models': cache_size,
        'methodology_url': 'https://rankmodel.github.io/rankmodel1/methodology.html',
        'api_docs_url': 'https://rankmodel.github.io/rankmodel1/api.html',
        'changelog_url': 'https://rankmodel.github.io/rankmodel1/changelog.json',
        'github_url': 'https://github.com/rankmodel/rankmodel1',
    }

@app.get("/score/{model_id:path}", response_model=ModelScore)
async def get_score(model_id: str, refresh: bool = False):
    try:
        if not refresh:
            cached_score = cache.get_score(model_id)
            if cached_score:
                return cached_score
        
        # Cache miss or refresh requested
        model_data = fetcher.fetch_model_info(model_id)
        if not model_data:
            raise HTTPException(status_code=404, detail="Model not found")
            
        eval_results = fetcher.fetch_eval_results(model_id)
        score = compute_composite_score(model_data, eval_results)
        cache.set_score(model_id, score)
        return score
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error scoring model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/badge/{model_id:path}")
async def get_badge(
    model_id: str, 
    type: str = Query('score', description='score|rank|tier|dimension|achievement'),
    dimension: Optional[str] = Query(None, description='e.g., benchmarks'),
    achievement_type: Optional[str] = Query(None, description='e.g., abliterated'),
    format: str = Query('svg')
):
    try:
        # Fetch score data
        score = cache.get_score(model_id)
        if not score:
            model_data = fetcher.fetch_model_info(model_id)
            if not model_data:
                raise HTTPException(status_code=404, detail="Model not found")
            eval_results = fetcher.fetch_eval_results(model_id)
            score = compute_composite_score(model_data, eval_results)
            cache.set_score(model_id, score)
            
        # Generate badge
        svg_content = badge_generator.generate_badge(
            model_id=model_id,
            score_data=score,
            badge_type=type,
            dimension=dimension,
            achievement_type=achievement_type
        )
        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        logging.error(f"Error generating badge for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(50, le=200),
    tier: Optional[str] = None,
    task: Optional[str] = None,
    offset: int = 0
):
    try:
        results = cache.get_leaderboard(limit=limit, offset=offset, tier=tier, task=task)
        total = cache.get_total_models(tier=tier, task=task)
        return {
            "total": total,
            "models": results,
            "page_info": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score/batch", response_model=List[ModelScore])
async def score_batch(request: BatchScoreRequest):
    if len(request.model_ids) > 20:
        raise HTTPException(status_code=400, detail="Cannot score more than 20 models at once")
        
    try:
        # Simple batch implementation
        results = []
        for model_id in request.model_ids:
            score = cache.get_score(model_id)
            if not score:
                model_data = fetcher.fetch_model_info(model_id)
                if model_data:
                    eval_results = fetcher.fetch_eval_results(model_id)
                    score = compute_composite_score(model_data, eval_results)
                    cache.set_score(model_id, score)
            if score:
                results.append(score)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/achievements/{model_id:path}")
async def get_model_achievements(model_id: str):
    try:
        model_data = cache.get_model(model_id)
        score = cache.get_score(model_id)
        if not model_data or not score:
            model_data = fetcher.fetch_model_info(model_id)
            if not model_data:
                raise HTTPException(status_code=404, detail="Model not found")
            eval_results = fetcher.fetch_eval_results(model_id)
            score = compute_composite_score(model_data, eval_results)
            cache.set_score(model_id, score)
        achievements = get_achievements(model_data, score, score.get('rank', 0))
        return achievements
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/embed/{model_id:path}")
async def get_embed(model_id: str):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                background-color: #0f0f23;
                color: white;
                font-family: sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                justify-content: center;
                align-items: center;
            }}
            img {{
                max-height: 28px;
            }}
        </style>
    </head>
    <body>
        <a href="/api/score/{model_id}" target="_blank">
            <img src="/badge/{model_id}?type=tier" alt="Tier Badge"/>
        </a>
        <a href="/api/score/{model_id}" target="_blank">
            <img src="/badge/{model_id}?type=score" alt="Score Badge"/>
        </a>
        <a href="/api/score/{model_id}" target="_blank">
            <img src="/badge/{model_id}?type=rank" alt="Rank Badge"/>
        </a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/compare")
async def compare_models_endpoint(
    model_a: str = Query(..., description="First model ID (e.g. mistralai/Mistral-7B-v0.1)"),
    model_b: str = Query(..., description="Second model ID")
):
    """Compare two models head-to-head with Bradley-Terry ELO-based win probability."""
    try:
        results = {}
        for mid in [model_a, model_b]:
            score = cache.get_score(mid)
            if not score:
                model_data = fetcher.fetch_model_info(mid)
                if not model_data:
                    raise HTTPException(status_code=404, detail=f"Model {mid} not found")
                eval_results = fetcher.fetch_eval_results(mid)
                score = compute_composite_score(model_data, eval_results)
                cache.set_score(mid, score)
            results[mid] = score
        comparison = compare_models_elo(results[model_a], results[model_b])
        return {
            "model_a": model_a,
            "model_b": model_b,
            "scores": {"a": results[model_a], "b": results[model_b]},
            "comparison": comparison
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error comparing {model_a} vs {model_b}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shields/{model_id:path}", include_in_schema=True)
async def shields_endpoint(model_id: str):
    """
    Shields.io-compatible JSON endpoint.
    Embed in any README with:
      ![ModelRank](https://img.shields.io/endpoint?url=https://YOUR_URL/shields/org/model)
    """
    score = cache.get_score(model_id)
    if not score:
        return {"schemaVersion": 1, "label": "ModelRank", "message": "unscored", "color": "lightgrey", "namedLogo": "huggingface"}
    tier = score.get("tier", "C")
    composite = score.get("composite", 0)
    color_map = {"S": "blueviolet", "A": "blue", "B": "brightgreen", "C": "yellow", "D": "red"}
    return {
        "schemaVersion": 1,
        "label": "ModelRank",
        "message": f"{composite:.0f} ({tier})",
        "color": color_map.get(tier, "grey"),
        "namedLogo": "huggingface",
        "logoColor": "white",
        "style": "flat-square",
    }

@app.get("/score/{model_id:path}/extended")
async def get_score_extended(model_id: str):
    """
    Returns the composite score plus the 10 extended metadata signals
    (context_window, vram_tier, license_score, finetune_friendly, multilingual,
     safety_score, update_velocity, inference_coverage, community_momentum, hub_completeness).
    """
    score = cache.get_score(model_id)
    if not score:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not yet scored. Use GET /score/{model_id} to score it first.")
    return score

@app.get('/trending')
async def get_trending(limit: int = 10):
    """
    Returns trending models based on community momentum + recency score.
    Updated daily by the static asset generator.
    """
    models = cache.get_leaderboard(limit=200)
    trending = []
    for rank, m in enumerate(models, 1):
        s = m.get('score', {})
        b = s.get('breakdown', {})
        comm = b.get('community', 0)
        rec = b.get('recency', b.get('freshness', 0))
        trend_score = comm * 0.6 + rec * 0.4
        if trend_score > 50:
            trending.append({
                'model_id': m['model_id'],
                'composite': s.get('composite', 0),
                'tier': s.get('tier', 'D'),
                'trend_score': round(trend_score, 1),
                'community_score': comm,
                'recency_score': rec,
                'global_rank': rank
            })
    trending.sort(key=lambda x: x['trend_score'], reverse=True)
    return {'trending': trending[:limit], 'total': len(trending)}

if __name__ == '__main__':
    uvicorn.run(app, host=API_HOST, port=API_PORT)

