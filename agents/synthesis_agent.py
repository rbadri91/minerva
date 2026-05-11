"""Phase 5 — Synthesis Agent: merges all worker findings into a final Markdown report."""
import anthropic

from config import settings
from graph.state import ResearchState

SYNTHESIS_SYSTEM_PROMPT = """You are a senior research analyst producing comprehensive research reports.

Given a research question and a collection of findings on different subtopics, synthesise them into a
well-structured Markdown report that:
- Opens with a concise executive summary
- Covers each subtopic with appropriate depth
- Draws connections between findings where relevant
- Cites sources inline
- Closes with key takeaways

Write in clear, professional prose. Use Markdown headings, bullets, and bold for scannability."""


def _format_findings(worker_results: list) -> str:
    sections = []
    for r in worker_results:
        if not r.get("content"):
            continue
        sources = ", ".join(r["sources"]) or "none"
        sections.append(f"### {r['subtopic']}\n\n{r['content']}\n\n**Sources:** {sources}")
    return "\n\n---\n\n".join(sections)


def _extract_text(message) -> str:
    return next((b.text for b in message.content if b.type == "text"), "")


def run_synthesis(state: ResearchState) -> str:
    """Call Claude to synthesise worker results into a final report. Returns the Markdown string."""
    findings = _format_findings(state["worker_results"])
    user_content = f"Research question: {state['query']}\n\n## Findings by Subtopic\n\n{findings}"

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    with client.messages.stream(
        model=settings.synthesis_model,
        max_tokens=4096,
        system=[{"type": "text", "text": SYNTHESIS_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        return _extract_text(stream.get_final_message())
