import anthropic

from config import settings
from graph.state import SubtopicPlan, WorkerResult
from tools.scraper_tools import scrape_urls
from tools.tavily_tools import search

READER_SYSTEM_PROMPT = """You are a research assistant specialising in deep reading and synthesis.
You will be given a subtopic and scraped web content from relevant pages.
Extract the most important information, insights, and details relevant to the subtopic.
Organise your response clearly with key findings."""


def run_reader_worker(subtopic_plan: SubtopicPlan) -> WorkerResult:
    """Scrape the top pages for a subtopic and summarise the content with Claude Haiku."""
    results = search(subtopic_plan["search_query"], max_results=3)

    if not results:
        return WorkerResult(
            subtopic=subtopic_plan["subtopic"],
            content=f"No pages found for: {subtopic_plan['search_query']}",
            sources=[],
            from_cache=False,
            worker_type="reader",
        )

    urls = [r["url"] for r in results if r["url"]]
    scraped = scrape_urls(urls)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.worker_model,
        max_tokens=1024,
        system=[{"type": "text", "text": READER_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": f"Subtopic: {subtopic_plan['subtopic']}\n\nScraped content:\n{scraped}",
            }
        ],
    )

    content = next((b.text for b in response.content if b.type == "text"), "")

    return WorkerResult(
        subtopic=subtopic_plan["subtopic"],
        content=content,
        sources=urls,
        from_cache=False,
        worker_type="reader",
    )
