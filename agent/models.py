from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Ticket:
    id: str
    text: str
    submitted_at: datetime
    user: Optional[str] = None


@dataclass
class ClassificationResult:
    category: str
    confidence: float


@dataclass
class RoutingResult:
    department: str


@dataclass
class RetrievedTicket:
    ticket_id: str
    text: str
    similarity: float
    resolution: str = ""


@dataclass
class ResolutionResult:
    suggested_steps: str


@dataclass
class ConfidenceResult:
    score: float
    tier: str


@dataclass
class RecurringResult:
    is_recurring: bool
    cluster_size: int = 0


@dataclass
class PipelineResult:
    ticket: Ticket
    classification: ClassificationResult
    routing: RoutingResult
    retrieved: List[RetrievedTicket]
    resolution: ResolutionResult
    confidence: ConfidenceResult
    recurring: RecurringResult
    escalated: bool
    remediation: dict