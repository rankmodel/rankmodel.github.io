"""
ModelRank Pricing & Plan Configuration

Revenue streams:
  1. Verified Pro Badges     - Model creators pay for premium embeddable badges
  2. Featured Leaderboard    - Sponsored placement in leaderboard (labeled)
  3. Research Reports        - PDF deep-dives via NotebookLM (per report or subscription)
  4. API Access Tiers        - Free / Pro / Enterprise REST API
  5. Org Certification       - Annual cert for org-wide model quality program
"""

PLANS = {
    'free': {
        'name': 'Free',
        'price_monthly': 0,
        'price_annual': 0,
        'api_calls_per_day': 50,
        'badge_types': ['score', 'tier'],
        'badge_styles': ['flat'],
        'leaderboard_placement': 'standard',
        'research_reports': 0,
        'compare_models': 2,
        'history_days': 0,
        'priority_indexing': False,
        'verified_checkmark': False,
        'custom_branding': False,
        'webhook_alerts': False,
        'csv_export': False,
        'description': 'Perfect for exploring ModelRank.',
    },
    'pro': {
        'name': 'Pro',
        'price_monthly': 29,
        'price_annual': 249,  # ~$20.75/mo billed annually
        'api_calls_per_day': 1000,
        'badge_types': ['score', 'tier', 'rank', 'dimension', 'achievement', 'animated'],
        'badge_styles': ['flat', 'default', 'glow', 'minimal'],
        'leaderboard_placement': 'standard',
        'research_reports': 3,       # per month
        'compare_models': 10,
        'history_days': 90,
        'priority_indexing': True,   # model re-scored within 1h of update
        'verified_checkmark': True,  # green checkmark on leaderboard
        'custom_branding': False,
        'webhook_alerts': True,      # alert when rank changes
        'csv_export': True,
        'description': 'For serious model creators and researchers.',
    },
    'featured': {
        'name': 'Featured',
        'price_monthly': 99,
        'price_annual': 899,
        'api_calls_per_day': 5000,
        'badge_types': ['score', 'tier', 'rank', 'dimension', 'achievement', 'animated', 'featured'],
        'badge_styles': ['flat', 'default', 'glow', 'minimal', 'premium'],
        'leaderboard_placement': 'featured',  # pinned to top with "Sponsored" label
        'research_reports': 10,
        'compare_models': 50,
        'history_days': 365,
        'priority_indexing': True,
        'verified_checkmark': True,
        'custom_branding': True,     # custom badge colors/logo
        'webhook_alerts': True,
        'csv_export': True,
        'description': 'Maximum visibility for your models.',
    },
    'enterprise': {
        'name': 'Enterprise',
        'price_monthly': None,       # custom pricing
        'price_annual': None,
        'api_calls_per_day': -1,     # unlimited
        'badge_types': 'all',
        'badge_styles': 'all',
        'leaderboard_placement': 'featured',
        'research_reports': -1,      # unlimited
        'compare_models': -1,
        'history_days': -1,
        'priority_indexing': True,
        'verified_checkmark': True,
        'custom_branding': True,
        'webhook_alerts': True,
        'csv_export': True,
        'white_label': True,         # run ModelRank as your own internal tool
        'sla': '99.9%',
        'dedicated_support': True,
        'description': 'For AI labs and enterprises. Custom contract.',
    }
}

# One-off products
PRODUCTS = {
    'research_report': {
        'name': 'Model Research Report',
        'price': 49,
        'description': '~5-min audio deep-dive + PDF summary via NotebookLM. Covers architecture, benchmarks, use cases, and comparisons.',
        'delivery': '15-30 minutes after purchase',
    },
    'featured_week': {
        'name': 'Featured Placement (7 days)',
        'price': 49,
        'description': 'Your model pinned to the top of the leaderboard with a "Featured" label for 7 days.',
    },
    'featured_month': {
        'name': 'Featured Placement (30 days)',
        'price': 149,
        'description': 'Your model at the top of the leaderboard for 30 days. Includes a Featured badge.',
    },
    'org_certification': {
        'name': 'Org Quality Certification (Annual)',
        'price': 999,
        'description': 'Annual ModelRank certification for your entire org. All models auto-scored, verified checkmark on all, quarterly review report, press kit assets.',
    },
}

# API rate limit overrides per plan key
API_LIMITS = {
    'free': {'per_day': 50, 'per_minute': 5},
    'pro': {'per_day': 1000, 'per_minute': 60},
    'featured': {'per_day': 5000, 'per_minute': 200},
    'enterprise': {'per_day': -1, 'per_minute': -1},
}

# Target customer segments and pitch angles
TARGET_SEGMENTS = [
    {
        'segment': 'Independent Model Creators',
        'description': 'Researchers/hackers who publish models to HF and want credibility.',
        'pain_point': 'No trusted third-party quality signal for their models.',
        'pitch': 'A ModelRank Pro badge on your model card is instant social proof that your model is benchmarked, efficient, and community-trusted.',
        'price_sensitivity': 'low',
        'recommended_plan': 'pro',
    },
    {
        'segment': 'AI Startups with Open Models',
        'description': 'Companies like Mistral, Cohere, etc. who open-source models as marketing.',
        'pain_point': 'Hard to differentiate from the noise. No neutral third-party ranking.',
        'pitch': 'ModelRank Featured listing puts you above the fold for every developer searching for the best model in your class.',
        'price_sensitivity': 'medium',
        'recommended_plan': 'featured',
    },
    {
        'segment': 'AI Labs & Research Orgs',
        'description': 'Hugging Face orgs, university labs, national AI initiatives.',
        'pain_point': 'Need internal model quality tracking + external credibility.',
        'pitch': 'Our Enterprise Certification program gives your entire org a verified quality program with quarterly reports and a press kit.',
        'price_sensitivity': 'low',
        'recommended_plan': 'enterprise',
    },
    {
        'segment': 'MLOps / Tooling Companies',
        'description': 'Companies building on top of open models (Together AI, Replicate, Anyscale).',
        'pain_point': 'Need to recommend the best models to customers; need a neutral ranker.',
        'pitch': 'Integrate ModelRank API to power your model selection UI. White-label available.',
        'price_sensitivity': 'low',
        'recommended_plan': 'enterprise',
    },
]
