from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class TopicPerformanceResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    attempts: int
    correct_answers: int
    score_percentage: Decimal
    status: Literal["strong", "good", "needs_practice"]
    last_updated: datetime