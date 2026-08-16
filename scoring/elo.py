"""ELO head-to-head rating for ModelRank.

Implements the standard ELO update used for model-vs-model comparisons
(human votes or LLM-judge "vibe-checks"). Ratings are persisted in
``data/modelrank.db`` (``elo_ratings``) and every comparison is logged as a
``reviews`` row so the history is auditable and replayable.
"""

from typing import Tuple

DEFAULT_RATING = 1500.0
K_FACTOR = 32.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """P(A beats B) under the ELO model: ``1 / (1 + 10^((Rb - Ra) / 400))``."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def probability_a_beats_b(rating_a: float, rating_b: float) -> float:
    """Readable alias of :func:`expected_score` for call sites."""
    return expected_score(rating_a, rating_b)


def update_ratings(
    rating_a: float,
    rating_b: float,
    outcome: float,
    k: float = K_FACTOR,
) -> Tuple[float, float]:
    """Return the new ``(rating_a, rating_b)`` after one comparison.

    ``outcome`` is ``1.0`` if A wins, ``0.0`` if B wins, ``0.5`` for a tie.
    """
    expected_a = expected_score(rating_a, rating_b)
    expected_b = 1.0 - expected_a
    new_a = rating_a + k * (outcome - expected_a)
    new_b = rating_b + k * ((1.0 - outcome) - expected_b)
    return new_a, new_b
