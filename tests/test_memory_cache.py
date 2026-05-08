"""Phase 4 gate: cache-hit routing skips web search when a result is already stored."""
import pytest
from graph.orchestrator import research_worker_node
from graph.state import ResearchState, SubtopicPlan
from tools.memory_tools import check_cache, store_in_cache

QUERY = "benefits of intermittent fasting for metabolic health"
SUBTOPIC = SubtopicPlan(
    subtopic="Metabolic benefits of intermittent fasting",
    search_query=QUERY,
    worker_type="search",
    index=0,
)

def _worker_state(subtopic: SubtopicPlan) -> ResearchState:
    return ResearchState(
        query="test",
        conversation_history=[],
        research_plan=[],
        current_subtopic=subtopic,
        worker_results=[],
        status_updates=[],
        final_report="",
        error=None,
    )


def test_cache_miss_then_hit():
    # Seed the cache with a known result
    store_in_cache(QUERY, "Cached summary about fasting.", ["https://example.com"])

    # check_cache should now return the stored result
    hit = check_cache(QUERY)
    assert hit is not None, "Expected a cache hit for the exact same query"
    content, sources = hit
    assert "fasting" in content.lower()
    assert sources == ["https://example.com"]


def test_worker_returns_from_cache_when_seeded():
    # Pre-seed the cache for this subtopic's search_query
    store_in_cache(QUERY, "Pre-cached fasting content.", ["https://cached.com"])

    result = research_worker_node(_worker_state(SUBTOPIC))

    worker_results = result["worker_results"]
    assert len(worker_results) == 1
    assert worker_results[0]["from_cache"] is True, "Worker should return cached result"
    assert "cache hit" in result["status_updates"][0]


def test_cache_miss_hits_web():
    novel_query = "extremely specific query that is definitely not cached xyzzy42"
    novel_subtopic = SubtopicPlan(
        subtopic="Novel subtopic",
        search_query=novel_query,
        worker_type="search",
        index=0,
    )

    result = research_worker_node(_worker_state(novel_subtopic))

    worker_results = result["worker_results"]
    assert len(worker_results) == 1
    assert worker_results[0]["from_cache"] is False, "Worker should hit the web for an uncached query"
