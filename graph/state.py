import operator
from typing import Annotated, Optional, TypedDict


class SubtopicPlan(TypedDict):
    subtopic: str
    search_query: str
    worker_type: str  # "search", "reader", or "both"
    index: int


class WorkerResult(TypedDict):
    subtopic: str
    content: str
    sources: list[str]
    from_cache: bool
    worker_type: str


class ResearchState(TypedDict):
    query: str
    conversation_history: Annotated[list[dict], operator.add]
    research_plan: list[SubtopicPlan]
    current_subtopic: Optional[SubtopicPlan]  # payload carrier for Send fan-out
    worker_results: Annotated[list[WorkerResult], operator.add]
    status_updates: Annotated[list[str], operator.add]
    final_report: str
    error: Optional[str]
