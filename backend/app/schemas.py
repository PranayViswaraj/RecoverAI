from pydantic import BaseModel, Field
from typing import Optional, List

class RecoveryDecision(BaseModel):
    recoverable: bool
    recovery_probability: float = Field(ge=0, le=1)
    recommended_action: str
    explanation: str
    confidence: float = Field(ge=0, le=1)
    expected_recovery: float = 0
    action_cost: float = 0
    expected_roi: float = 0
    risk_score: float = 0
    guardrail_status: str = "AUTO"

class ExecuteResponse(BaseModel):
    payment_id: str
    action: str
    status: str
    message: str
    payment_link_url: Optional[str] = None

class DashboardResponse(BaseModel):
    revenue_at_risk: float
    recoverable_revenue: float
    recovered_revenue: float
    recovery_rate: float
    failed_payments: int
    recoverable_count: int
    pending_actions: int
    escalated_count: int
    expected_recovery: float
