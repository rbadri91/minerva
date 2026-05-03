import anthropic

from config import settings
from graph.state import SubtopicPlan, WorkerResult
from tools.tavily_tools import search

SEARCH_SYSTEM_PROMPT = """You are a research assistant. You will be given a subtopic and web search results.
Synthesize the results into a clear, factual summary focused on the subtopic.
Include key facts, data points, and insights. Be concise but thorough."""


def run_search_worker(subtopic_plan: SubtopicPlan) -> WorkerResult:
    """Search the web for a subtopic and summarise the findings with Claude Haiku."""
    results = search(subtopic_plan["search_query"])

    if not results:
        return WorkerResult(
            subtopic=subtopic_plan["subtopic"],
            content=f"No search results found for: {subtopic_plan['search_query']}",
            sources=[],
            from_cache=False,
            worker_type="search",
        )

    sources = [r["url"] for r in results if r["url"]]
    search_text = "\n\n".join(
        f"**{r['title']}** ({r['url']})\n{r['content']}" for r in results
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.worker_model,
        max_tokens=1024,
        system=[{"type": "text", "text": SEARCH_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": f"Subtopic: {subtopic_plan['subtopic']}\n\nSearch results:\n{search_text}",
            }
        ],
    )

    content = next((b.text for b in response.content if b.type == "text"), "")

    return WorkerResult(
        subtopic=subtopic_plan["subtopic"],
        content=content,
        sources=sources,
        from_cache=False,
        worker_type="search",
    )
