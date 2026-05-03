import anthropic

from config import settings
from graph.state import ResearchState, SubtopicPlan

MANAGER_SYSTEM_PROMPT = """You are Minerva's research manager. Your job is to decompose a user's research query into a structured plan of focused subtopics that can be researched in parallel.

For each subtopic:
- Make it specific and non-overlapping with the others
- Write a targeted search query optimised for web search
- Choose worker_type: "search" for factual/current info, "reader" for deep dives on specific pages, "both" for complex topics

Produce between 2 and {max_subtopics} subtopics. Fewer is better when the query is already focused.""".format(
    max_subtopics=settings.max_subtopics
)

RESEARCH_PLAN_TOOL = {
    "name": "create_research_plan",
    "description": "Create a structured research plan decomposing the query into parallel subtopics.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subtopics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subtopic": {"type": "string", "description": "Focused subtopic title"},
                        "search_query": {"type": "string", "description": "Optimised web search query"},
                        "worker_type": {
                            "type": "string",
                            "enum": ["search", "reader", "both"],
                            "description": "Which worker strategy to use",
                        },
                    },
                    "required": ["subtopic", "search_query", "worker_type"],
                },
                "minItems": 2,
                "maxItems": settings.max_subtopics,
            }
        },
        "required": ["subtopics"],
    },
}


def create_research_plan(query: str, conversation_history: list[dict] | None = None) -> list[SubtopicPlan]:
    """Call Claude to decompose query into a list of SubtopicPlan dicts."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": query})

    response = client.messages.create(
        model=settings.manager_model,
        max_tokens=2048,
        system=[{"type": "text", "text": MANAGER_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[RESEARCH_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_research_plan"},
        messages=messages,
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError("Manager agent did not return a research plan")

    return [
        SubtopicPlan(
            subtopic=s["subtopic"],
            search_query=s["search_query"],
            worker_type=s["worker_type"],
            index=i,
        )
        for i, s in enumerate(tool_block.input["subtopics"])
    ]


def run_manager(state: ResearchState) -> dict:
    """LangGraph node: produces research_plan from the current query."""
    try:
        plan = create_research_plan(state["query"], state.get("conversation_history"))
    except Exception as exc:
        return {"error": str(exc), "status_updates": [f"Manager failed: {exc}"]}

    status = [f"Research plan: {len(plan)} subtopics"] + [
        f"  [{s['index']}] {s['subtopic']} ({s['worker_type']})" for s in plan
    ]
    return {"research_plan": plan, "status_updates": status}
