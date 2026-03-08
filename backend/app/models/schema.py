from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class TelemetryLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    truck_id: str
    destination: str
    risk_score: int
    ai_prediction: str
    ai_reasoning: str
    ai_directive: str
    human_approved: bool = Field(default=False)
