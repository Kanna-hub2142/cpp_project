from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import string
from typing import Dict
from django.utils import timezone

# Default mapping from order status to extra days
DEFAULT_STATUS_DAYS: Dict[str, int] = {
    "ORDERED": 10,
    "PROCESSING": 7,
    "TRANSIT": 3,
    "READY_FOR_DELIVERY": 1,
    "DELIVERED": 0,
}


@dataclass
class OrderEstimate:
    order_id: str
    status: str
    estimated_delivery: datetime


class OrderUtils:

    def __init__(self, status_days: Dict[str, int] | None = None):
        self.status_days = {k.upper(): v for k, v in (status_days or DEFAULT_STATUS_DAYS).items()}

    def generate_order_id(self, prefix: str = "ORD") -> str:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rand = "".join(random.choices(string.digits, k=4))
        return f"{prefix}-{ts}{rand}"

    def estimate_delivery_by_status(self, status: str) -> datetime:
        key = status.upper().replace(" ", "_")
        days = self.status_days.get(key, self.status_days["ORDERED"])
        return timezone.now() + timedelta(days=days)

    def create_order_estimate(self, status: str) -> OrderEstimate:
        order_id = self.generate_order_id()
        normalized = status.upper().replace(" ", "_")
        eta = self.estimate_delivery_by_status(normalized)

        return OrderEstimate(
            order_id=order_id,
            status=normalized,
            estimated_delivery=eta
        )
