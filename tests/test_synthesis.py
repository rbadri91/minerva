"""Phase 5 gate: synthesis agent produces a well-formed Markdown report."""
import pytest

from agents.synthesis_agent import run_synthesis
from graph.orchestrator import build_graph
from graph.state import ResearchState, WorkerResult


def _make_state(worker_results: list[WorkerResult]) -> ResearchState:
    return {
        "query": "What are the pros and cons of solar energy?",
        "conversation_history": [],
        "research_plan": [],
        "current_subtopic": None,
        "worker_results": worker_results,
        "status_updates": [],
        "final_report": "",
        "error": None,
    }


# ── Isolation tests (no web / no manager) ─────────────────────────────────────

def test_synthesis_returns_nonempty_markdown():
    """Synthesis agent returns a non-empty string given pre-built worker results."""
    results: list[WorkerResult] = [
        {
            "subtopic": "Cost trends",
            "content": "Solar panel prices have dropped over 90% in the last decade.",
            "sources": ["https://example.com/solar-costs"],
            "from_cache": False,
            "worker_type": "search",
        },
        {
            "subtopic": "Environmental impact",
            "content": "Solar energy produces no direct CO2 emissions during operation.",
            "sources": ["https://example.com/solar-env"],
            "from_cache": False,
            "worker_type": "search",
        },
    ]
    report = run_synthesis(_make_state(results))

    assert report, "run_synthesis returned an empty string"
    assert len(report) > 100, f"Report suspiciously short ({len(report)} chars)"


def test_format_findings_skips_empty_content():
    """_format_findings must silently skip worker results that have no content."""
    from agents.synthesis_agent import _format_findings

    results = [
        {"subtopic": "A", "content": "", "sources": [], "from_cache": False, "worker_type": "search"},
        {"subtopic": "B", "content": "Real content.", "sources": ["https://b.com"], "from_cache": False, "worker_type": "search"},
    ]
    out = _format_findings(results)
    assert "Real content." in out
    assert "### A" not in out


def test_synthesis_includes_subtopic_content():
    """Report should reference both subtopics passed in."""
    results: list[WorkerResult] = [
        {
            "subtopic": "Storage challenges",
            "content": "Battery storage remains expensive and limits overnight solar use.",
            "sources": ["https://example.com/storage"],
            "from_cache": False,
            "worker_type": "search",
        },
        {
            "subtopic": "Grid integration",
            "content": "Intermittency requires grid operators to balance load with other sources.",
            "sources": ["https://example.com/grid"],
            "from_cache": False,
            "worker_type": "search",
        },
    ]
    report = run_synthesis(_make_state(results))

    assert any(kw in report.lower() for kw in ("storage", "battery", "grid", "intermit")), (
        "Report doesn't seem to reference the provided subtopic content"
    )


# ── Full graph integration test ───────────────────────────────────────────────

def test_full_graph_produces_report():
    """End-to-end: graph runs manager + workers + synthesis and emits a final report."""
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

    report = result.get("final_report", "")
    assert report, "Graph did not produce a final_report"
    assert len(report) > 200, f"Final report suspiciously short ({len(report)} chars)"
    assert "#" in report, "Report doesn't contain any Markdown headings"
