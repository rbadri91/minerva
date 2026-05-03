"""Phase 3 gate: given a research plan, workers return findings for all subtopics."""
from graph.orchestrator import build_graph
from graph.state import ResearchState


def test_workers_return_results_for_all_subtopics():
    initial: ResearchState = {
        "query": "What are the pros and cons of solar energy?",
        "conversation_history": [],
        "research_plan": [],
        "current_subtopic": None,
        "worker_results": [],
        "status_updates": [],
        "final_report": "",
        "error": None,
    }

    result = build_graph().invoke(initial)

    plan = result["research_plan"]
    worker_results = result["worker_results"]

    assert len(plan) >= 2, "Manager should produce at least 2 subtopics"
    assert len(worker_results) == len(plan), (
        f"Expected one WorkerResult per subtopic ({len(plan)}), got {len(worker_results)}"
    )

    for wr in worker_results:
        assert wr["content"], f"Worker result for '{wr['subtopic']}' has no content"
        assert isinstance(wr["sources"], list), "sources must be a list"
