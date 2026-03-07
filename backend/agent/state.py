from typing import TypedDict, Annotated
from pydantic import BaseModel, Field

class AIAnalysis(BaseModel):
    prediction: str = Field(description="Delay prediction string (e.g., 'High Probability of Delay', 'Minor Delay Expected', 'On Time Expected')")
    risk_score: int = Field(description="Calculated risk score 0-100")
    reasoning: str = Field(description="Explanation of the AI's reasoning based on weather, traffic, and events")
    action_directive: str = Field(description="Action the truck should take, e.g., 'REROUTE TO ALTERNATE WAREHOUSE. ...' or 'Continue on current route.'")
    requires_human_approval: bool = Field(description="True if risk is high and human should review")

class AgentState(TypedDict):
    telemetry: dict
    ml_label: int
    ml_risk_score: int
    analysis: AIAnalysis
