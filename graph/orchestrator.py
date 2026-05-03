from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.manager_agent import run_manager
from graph.state import ResearchState


def plan_node(state: ResearchState) -> dict:
    return run_manager(state)


def research_worker_node(state: ResearchState) -> dict:
    # TODO Phase 3: call search_agent / reader_agent based on current_subtopic
    return {"worker_results": [], "status_updates": ["[placeholder] Worker step"]}


def synthesis_node(state: ResearchState) -> dict:
    # TODO Phase 5: call synthesis_agent to produce the final report
    return {"final_report": "[placeholder] Final report", "status_updates": ["[placeholder] Synthesis step"]}


def dispatch_workers(state: ResearchState) -> list[Send]:
    plan = state.get("research_plan")
    if not plan:
        return [Send("synthesize", state)]
    return [Send("research_worker", {**state, "current_subtopic": s}) for s in plan]


def build_graph() -> StateGraph:
    builder = StateGraph(ResearchState)
    builder.add_node("plan", plan_node)
    builder.add_node("research_worker", research_worker_node)
    builder.add_node("synthesize", synthesis_node)

    builder.add_edge(START, "plan")
    builder.add_conditional_edges("plan", dispatch_workers, ["research_worker", "synthesize"])
    builder.add_edge("research_worker", "synthesize")
    builder.add_edge("synthesize", END)

    return builder.compile()


graph = build_graph()
