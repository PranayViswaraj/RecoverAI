from dataclasses import dataclass
from typing import Optional

@dataclass
class Transaction:
    payment_id: str
    customer_id: str
    order_id: str
    amount: float
    status: str
    failure_reason: Optional[str]
    transaction_type: str
    timestamp: str
