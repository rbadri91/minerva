"""Cache check / store interface used by research_worker_node."""
from graph.state import SubtopicPlan, WorkerResult
from tools.memory_tools import check_cache, store_in_cache


def lookup(subtopic_plan: SubtopicPlan) -> WorkerResult | None:
    """Return a WorkerResult from cache if a hit exists, else None."""
    cached = check_cache(subtopic_plan["search_query"])
    if cached is None:
        return None
    content, sources = cached
    return WorkerResult(
        subtopic=subtopic_plan["subtopic"],
        content=content,
        sources=sources,
        from_cache=True,
        worker_type="memory",
    )


def store(subtopic_plan: SubtopicPlan, content: str, sources: list[str]) -> None:
    store_in_cache(subtopic_plan["search_query"], content, sources)
