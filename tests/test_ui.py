import ui.app as ui
from data.cache import ModelCache


def _seed(monkeypatch, tmp_path):
    c = ModelCache(db_path=str(tmp_path / "ui.db"))
    c.set_model("A", {"model_id": "A", "params": 7e9})
    c.set_model("B", {"model_id": "B", "params": 13e9})
    c.set_score("A", {"composite": 80, "tier": "A",
                      "breakdown": {"benchmarks": 90, "efficiency": 50, "community": 60, "recency": 70, "reproducibility": 0}})
    c.set_score("B", {"composite": 70, "tier": "B",
                      "breakdown": {"benchmarks": 60, "efficiency": 90, "community": 50, "recency": 60, "reproducibility": 0}})
    monkeypatch.setattr(ui, "cache", c)
    return c


def test_recommend_ui(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    out = ui.recommend_ui("coding")
    assert "A" in out and "B" in out


def test_judge_human_ui(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    out = ui.judge_human_ui("A", "B", "A wins")
    assert "A wins" in out
    assert "ELO" in out and "1516.0" in out  # A's ELO rose after a win


def test_elo_ui(monkeypatch, tmp_path):
    c = _seed(monkeypatch, tmp_path)
    ui.judge_human_ui("A", "B", "A wins")
    out = ui.elo_ui("A")
    assert "matches" in out
    # unknown model still renders
    assert "no elo record" in ui.elo_ui("Z").lower()


def test_judge_llm_ui(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    import scoring.judge as jm

    def fake(model_a, model_b, cache=None, llm_call=None, judge_id=None):
        return {"review_id": "x", "verdict": "A", "rationale": "A is better",
                "model_a": model_a, "model_b": model_b}

    monkeypatch.setattr(jm, "run_llm_judge", fake)
    out = ui.judge_llm_ui("A", "B")
    assert "A" in out
    assert "A is better" in out
