from pydantic import BaseModel
from typing import List, Optional

class SourceItem(BaseModel):
    url: str
    source_type: str
    date: Optional[str] = None
    authority_score: float
    relevance_score: float
    claims: List[str]

class ConflictItem(BaseModel):
    topic: str
    sources: List[str]
    resolution: str

class GapItem(BaseModel):
    missing: str
    next_query: str

class RunOutput(BaseModel):
    topic: str
    sources: List[SourceItem]
    conflicts: List[ConflictItem]
    gaps: List[GapItem]
    synthesis: str
