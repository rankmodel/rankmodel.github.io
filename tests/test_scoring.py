"""
Unit tests for the ModelRank scoring engine.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring.benchmarks import normalize_benchmark_scores, get_benchmark_score_for_model
from scoring.community import compute_community_score
from scoring.recency import compute_recency_score, score_to_freshness_label
from scoring.efficiency import compute_efficiency_score, estimate_param_count_from_name
from scoring.reproducibility import compute_repro_score
from scoring.engine import compute_composite_score, score_to_tier


class TestBenchmarkScoring:
    def test_empty_eval_results_returns_zero(self):
        assert normalize_benchmark_scores([]) == 0.0

    def test_known_benchmark_scored(self):
        evals = [{'dataset_id': 'mmlu-pro', 'value': 80.0}]
        score = normalize_benchmark_scores(evals)
        assert 0.0 <= score <= 100.0

    def test_score_clamped_to_100(self):
        evals = [{'dataset_id': 'mmlu-pro', 'value': 150.0}]
        score = normalize_benchmark_scores(evals)
        assert score <= 100.0

    def test_score_clamped_to_zero(self):
        evals = [{'dataset_id': 'mmlu-pro', 'value': -10.0}]
        score = normalize_benchmark_scores(evals)
        assert score >= 0.0

    def test_alias_resolution(self):
        evals = [{'dataset_id': 'mmlu', 'value': 70.0}]
        score = normalize_benchmark_scores(evals)
        assert score > 0.0

    def test_unknown_benchmark_ignored(self):
        evals = [{'dataset_id': 'unknown_bench_xyz', 'value': 99.0}]
        score = normalize_benchmark_scores(evals)
        assert score == 0.0

    def test_multiple_benchmarks(self):
        evals = [
            {'dataset_id': 'mmlu-pro', 'value': 80.0},
            {'dataset_id': 'gsm8k', 'value': 70.0},
        ]
        score = normalize_benchmark_scores(evals)
        assert 0.0 < score <= 100.0


class TestCommunityScoring:
    def test_zero_activity_returns_low_score(self):
        data = {'downloads': 0, 'likes': 0}
        assert compute_community_score(data) == 0.0

    def test_popular_model_high_score(self):
        data = {'downloads': 1_000_000, 'likes': 50_000}
        score = compute_community_score(data)
        assert score > 50.0

    def test_score_bounded(self):
        data = {'downloads': 999_999_999, 'likes': 999_999_999}
        score = compute_community_score(data)
        assert 0.0 <= score <= 100.0


class TestRecencyScoring:
    def test_just_released_model(self):
        from datetime import datetime, timedelta
        recent = (datetime.now() - timedelta(days=1)).isoformat()
        score = compute_recency_score(recent)
        assert score >= 90.0

    def test_old_model_lower_score(self):
        score_old = compute_recency_score('2020-01-01T00:00:00')
        score_new = compute_recency_score('2025-01-01T00:00:00')
        assert score_old < score_new

    def test_invalid_date_returns_zero(self):
        assert compute_recency_score('not-a-date') == 0.0

    def test_freshness_labels(self):
        assert score_to_freshness_label(95) == 'Just Released'
        assert score_to_freshness_label(75) == 'Fresh'
        assert score_to_freshness_label(55) == 'Recent'
        assert score_to_freshness_label(35) == 'Aging'
        assert score_to_freshness_label(10) == 'Legacy'


class TestEfficiencyScoring:
    def test_param_extraction_7b(self):
        count = estimate_param_count_from_name('mistralai/Mistral-7B-v0.1')
        assert count == 7_000_000_000

    def test_param_extraction_moe(self):
        count = estimate_param_count_from_name('mistralai/Mixtral-8x7B-v0.1')
        assert count == 56_000_000_000

    def test_no_param_count_returns_50(self):
        score = compute_efficiency_score({'param_count': None}, 80.0)
        assert score == 50.0

    def test_quantized_bonus(self):
        data = {'param_count': 7_000_000_000, 'is_quantized': True}
        score_q = compute_efficiency_score(data, 80.0)
        data2 = {'param_count': 7_000_000_000, 'is_quantized': False}
        score_nq = compute_efficiency_score(data2, 80.0)
        assert score_q > score_nq


class TestReproducibilityScoring:
    def test_empty_results_returns_zero(self):
        assert compute_repro_score([]) == 0.0

    def test_verified_results_high_score(self):
        evals = [{'verified': True, 'dataset_id': 'mmlu', 'source': 'verified'}] * 3
        score = compute_repro_score(evals)
        assert score >= 100.0

    def test_diversity_bonus(self):
        evals = [
            {'verified': False, 'dataset_id': f'bench_{i}', 'source': 'unknown'}
            for i in range(3)
        ]
        score = compute_repro_score(evals)
        assert score >= 20.0  # Should get diversity bonus


class TestCompositeEngine:
    def test_score_to_tier_s(self):
        assert score_to_tier(95) == 'S'

    def test_score_to_tier_a(self):
        assert score_to_tier(85) == 'A'

    def test_score_to_tier_b(self):
        assert score_to_tier(75) == 'B'

    def test_score_to_tier_c(self):
        assert score_to_tier(65) == 'C'

    def test_score_to_tier_d(self):
        assert score_to_tier(50) == 'D'

    def test_composite_score_structure(self):
        model_data = {
            'id': 'test/model',
            'downloads': 100000,
            'likes': 5000,
            'last_modified': '2025-06-01T00:00:00',
            'param_count': 7_000_000_000,
            'is_quantized': False,
            'is_abliterated': False,
        }
        evals = [{'dataset_id': 'mmlu-pro', 'value': 75.0, 'verified': True, 'source': 'verified', 'task_id': 'test'}]
        result = compute_composite_score(model_data, evals)
        assert 'composite' in result
        assert 'tier' in result
        assert 'breakdown' in result
        assert 0.0 <= result['composite'] <= 100.0
