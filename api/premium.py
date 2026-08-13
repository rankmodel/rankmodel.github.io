"""
ModelRank Premium API Routes

Handles plan management, featured badge generation, API key validation,
and premium-only endpoints.
"""
import os
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel

from config.pricing import PLANS, PRODUCTS, API_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/premium', tags=['Premium'])


# ---------------------------------------------------------------------------
# Simple in-memory API key store (replace with DB in production)
# ---------------------------------------------------------------------------
_API_KEYS: Dict[str, Dict[str, Any]] = {}


def _get_plan_for_key(api_key: str) -> Optional[str]:
    """Return plan name for a given API key, or None if not found."""
    entry = _API_KEYS.get(api_key)
    if entry and (entry.get('expires_at') is None or entry['expires_at'] > time.time()):
        return entry.get('plan', 'free')
    return None


def get_api_key_plan(x_api_key: Optional[str] = Header(None, alias='X-API-Key')) -> str:
    """FastAPI dependency: resolves plan from X-API-Key header. Defaults to 'free'."""
    if not x_api_key:
        return 'free'
    plan = _get_plan_for_key(x_api_key)
    if plan is None:
        raise HTTPException(status_code=401, detail='Invalid or expired API key.')
    return plan


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class IssueKeyRequest(BaseModel):
    plan: str
    label: str              # human label e.g. org name
    expires_days: Optional[int] = 30
    admin_secret: str       # simple admin password for now


class PlanInfoResponse(BaseModel):
    plan: str
    features: Dict[str, Any]
    api_limits: Dict[str, Any]


class FeaturedRequest(BaseModel):
    model_id: str
    plan: str = 'featured'
    duration_days: int = 30
    contact_email: str
    message: Optional[str] = None


class ReportRequest(BaseModel):
    model_id: str
    contact_email: str
    focus: Optional[str] = 'Focus on the technical architecture, benchmarks, and best use cases for this AI model.'


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get('/plans')
def list_plans():
    """List all available plans and pricing."""
    return {
        'plans': PLANS,
        'products': PRODUCTS,
    }


@router.get('/my-plan', response_model=PlanInfoResponse)
def get_my_plan(plan: str = Depends(get_api_key_plan)):
    """Return the plan details for the authenticated API key."""
    plan_data = PLANS.get(plan, PLANS['free'])
    limits = API_LIMITS.get(plan, API_LIMITS['free'])
    return PlanInfoResponse(plan=plan, features=plan_data, api_limits=limits)


@router.post('/issue-key', include_in_schema=False)
def issue_api_key(req: IssueKeyRequest):
    """Admin endpoint: issue a new API key for a plan. Secured by admin secret."""
    admin_secret = os.getenv('MODELRANK_ADMIN_SECRET', 'changeme')
    if req.admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail='Invalid admin secret.')
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f'Unknown plan: {req.plan}')
    
    key = 'mr_' + secrets.token_urlsafe(32)
    expires_at = time.time() + (req.expires_days * 86400) if req.expires_days else None
    _API_KEYS[key] = {
        'plan': req.plan,
        'label': req.label,
        'created_at': time.time(),
        'expires_at': expires_at,
    }
    logger.info(f'Issued API key for plan={req.plan}, label={req.label}')
    return {
        'api_key': key,
        'plan': req.plan,
        'label': req.label,
        'expires_at': datetime.fromtimestamp(expires_at).isoformat() if expires_at else None,
        'message': f'Keep this key safe. Pass it as X-API-Key header on all requests.',
    }


@router.post('/featured/request')
def request_featured_placement(req: FeaturedRequest):
    """
    Request featured leaderboard placement.
    In production, this would trigger a Stripe checkout or sales email.
    """
    logger.info(f'Featured placement request: model={req.model_id}, email={req.contact_email}')
    # TODO: integrate Stripe checkout / send to CRM
    return {
        'status': 'received',
        'model_id': req.model_id,
        'plan': req.plan,
        'duration_days': req.duration_days,
        'message': f'Thanks! We will contact {req.contact_email} within 24h to complete your Featured placement.',
        'pricing': PRODUCTS.get('featured_month', {}),
        'next_steps': [
            'Our team will send you a Stripe payment link.',
            'Once confirmed, your model will appear in the Featured section within 1 hour.',
            'You will receive weekly rank-change email alerts.',
        ]
    }


@router.post('/report/request')
def request_research_report(req: ReportRequest):
    """
    Request a ModelRank Research Report (NotebookLM audio + PDF summary).
    """
    logger.info(f'Report request: model={req.model_id}, email={req.contact_email}')
    return {
        'status': 'received',
        'model_id': req.model_id,
        'message': f'Research report request received for {req.model_id}.',
        'pricing': PRODUCTS['research_report'],
        'next_steps': [
            'We will send a payment link to your email.',
            'After payment, generation begins immediately (15-30 min).',
            'You will receive an audio file (.m4a) and a PDF summary.',
        ]
    }


@router.get('/pitch')
def get_pitch_kit():
    """Return the ModelRank pitch kit for reaching out to model creators."""
    from config.pricing import TARGET_SEGMENTS
    return {
        'tagline': 'The trust layer for open AI models.',
        'one_liner': 'ModelRank gives your HuggingFace models a composite score, tier badge, leaderboard rank, and research report — so developers can instantly evaluate quality.',
        'value_props': [
            '🏆 Third-party credibility: A ModelRank badge signals your model is independently scored.',
            '📈 Discoverability: Featured models appear at the top of the leaderboard for thousands of devs.',
            '📊 Deep analytics: Track your score history, compare vs competitors, get improvement suggestions.',
            '🎙️ Research report: Auto-generated audio + PDF deep-dive from your model card.',
            '⚡ Priority indexing: Re-scored within 1h of every model update.',
        ],
        'social_proof': {
            'note': 'Add real stats here as they accumulate.',
            'placeholders': [
                'X models scored',
                'Y badge embeds across GitHub repos',
                'Z API calls served',
            ]
        },
        'target_segments': TARGET_SEGMENTS,
        'cta': 'Email hello@modelrank.dev or open a GitHub issue tagged [Pro Request].',
    }


@router.get('/badge/{model_id:path}')
def get_premium_badge(
    model_id: str,
    style: str = Query('animated', description='animated|glow|featured|minimal'),
    plan: str = Depends(get_api_key_plan)
):
    """
    Generate a premium badge. Requires Pro or Featured plan.
    Pass your API key as X-API-Key header.
    """
    allowed = PLANS.get(plan, PLANS['free']).get('badge_styles', [])
    # Map style to plan requirement
    premium_styles = {'animated', 'glow', 'featured', 'minimal', 'premium'}
    if style in premium_styles and plan == 'free':
        raise HTTPException(
            status_code=402,
            detail=f'Style "{style}" requires a Pro or Featured plan. See /premium/plans.'
        )
    from data.cache import ModelCache
    from data.fetcher import HFDataFetcher
    from scoring.engine import compute_composite_score
    from badges.premium_generator import PREMIUM_BADGE_GENERATORS, generate_animated_score_badge
    from fastapi.responses import Response

    cache = ModelCache()
    fetcher = HFDataFetcher()

    score = cache.get_score(model_id)
    if not score:
        model_data = fetcher.fetch_model_info(model_id)
        if not model_data:
            raise HTTPException(status_code=404, detail='Model not found')
        eval_results = fetcher.fetch_eval_results(model_id)
        score = compute_composite_score(model_data, eval_results)
        cache.set_score(model_id, score)

    composite = score.get('composite', 0)
    tier = score.get('tier', 'C')

    gen = PREMIUM_BADGE_GENERATORS.get(style, generate_animated_score_badge)
    if style == 'featured':
        svg = gen(model_id, composite, tier)
    elif style == 'glow':
        svg = gen(tier)
    else:
        svg = gen(composite, tier)

    return Response(content=svg, media_type='image/svg+xml')
