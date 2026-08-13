from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Dict
from datetime import datetime

class ModelData(BaseModel):
    id: str
    downloads: int = 0
    likes: int = 0
    tags: List[str] = Field(default_factory=list)
    last_modified: Optional[Union[str, datetime]] = None
    created_at: Optional[Union[str, datetime]] = None

    @field_validator('last_modified', 'created_at', mode='before')
    @classmethod
    def coerce_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    pipeline_tag: Optional[str] = None
    library_name: Optional[str] = None
    param_count: Optional[int] = None
    is_abliterated: bool = False
    is_quantized: bool = False
    quantization_formats: List[str] = Field(default_factory=list)
    trending_score: float = 0.0

class EvalResult(BaseModel):
    model_id: str
    dataset_id: str
    task_id: str
    value: float
    verified: bool = False
    source: str = "unknown"

class ScoreBreakdown(BaseModel):
    benchmark_score: float = 0.0
    efficiency_score: float = 0.0
    community_score: float = 0.0
    recency_score: float = 0.0
    repro_score: float = 0.0

class ModelScore(BaseModel):
    model_id: str
    composite: float
    breakdown: Dict[str, float]
    rank: Optional[int] = None
    tier: Optional[str] = None
    computed_at: datetime = Field(default_factory=datetime.now)

class BadgeRequest(BaseModel):
    model_id: str
    badge_type: str
    style: str = "flat"

class Achievement(BaseModel):
    model_id: str
    achievement_type: str
    icon: str
    label: str
    color: str
    awarded_at: datetime = Field(default_factory=datetime.now)

class LeaderboardEntry(BaseModel):
    rank: int
    model_id: str
    composite_score: float
    tier: str
    downloads: int
    likes: int
    pipeline_tag: Optional[str] = None
    achievements: List[Achievement] = Field(default_factory=list)
