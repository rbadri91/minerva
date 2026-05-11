from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.manager_agent import run_manager
from agents.memory_agent import lookup, store
from agents.reader_agent import run_reader_worker
from agents.search_agent import run_search_worker
from agents.synthesis_agent import run_synthesis
from graph.state import ResearchState, WorkerResult


def plan_node(state: ResearchState) -> dict:
    return run_manager(state)


def research_worker_node(state: ResearchState) -> dict:
    subtopic = state["current_subtopic"]

    # Phase 4: memory-first — skip web if cache hit
    cached = lookup(subtopic)
    if cached is not None:
        label = f"Worker [{subtopic['index']}] '{subtopic['subtopic']}': cache hit"
        return {"worker_results": [cached], "status_updates": [label]}

    worker_type = subtopic["worker_type"]

    if worker_type == "reader":
        result: WorkerResult = run_reader_worker(subtopic)
    elif worker_type == "both":
        search_result = run_search_worker(subtopic)
        reader_result = run_reader_worker(subtopic)
        result = WorkerResult(
            subtopic=subtopic["subtopic"],
            content=search_result["content"] + "\n\n" + reader_result["content"],
            sources=list({*search_result["sources"], *reader_result["sources"]}),
            from_cache=False,
            worker_type="both",
        )
    else:
        result = run_search_worker(subtopic)

    store(subtopic, result["content"], result["sources"])

    label = f"Worker [{subtopic['index']}] '{subtopic['subtopic']}': done"
    return {"worker_results": [result], "status_updates": [label]}


def synthesis_node(state: ResearchState) -> dict:
    report = run_synthesis(state)
    return {"final_report": report, "status_updates": ["Synthesis complete"]}


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
