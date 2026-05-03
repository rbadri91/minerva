"""Phase 2 gate: manager agent returns a valid research plan for a test query."""
import pytest

from agents.manager_agent import create_research_plan
from config import settings


def test_research_plan_structure():
    plan = create_research_plan("What are the key differences between SQL and NoSQL databases?")

    assert 2 <= len(plan) <= settings.max_subtopics, (
        f"Expected 2–{settings.max_subtopics} subtopics, got {len(plan)}"
    )

    for i, subtopic in enumerate(plan):
        assert subtopic["subtopic"], f"subtopic[{i}] missing 'subtopic'"
        assert subtopic["search_query"], f"subtopic[{i}] missing 'search_query'"
        assert subtopic["worker_type"] in ("search", "reader", "both"), (
            f"subtopic[{i}] invalid worker_type: {subtopic['worker_type']}"
        )
        assert subtopic["index"] == i, f"subtopic[{i}] has wrong index: {subtopic['index']}"
