"""Phase 5 — Streamlit UI for Minerva deep research assistant."""
import streamlit as st

from graph.orchestrator import build_graph
from graph.state import ResearchState

st.set_page_config(page_title="Minerva Research Assistant", page_icon="🔬", layout="wide")
st.title("Minerva — Deep Research Assistant")

query = st.text_input("Research question", placeholder="What are the implications of quantum computing for cryptography?")

run_btn = st.button("Research", type="primary", disabled=not query.strip())

if run_btn and query.strip():
    initial: ResearchState = {
        "query": query,
        "conversation_history": [],
        "research_plan": [],
        "current_subtopic": None,
        "worker_results": [],
        "status_updates": [],
        "final_report": "",
        "error": None,
    }

    status_placeholder = st.empty()
    report_placeholder = st.empty()

    status_lines: list[str] = []
    final_report = ""

    with st.spinner("Running research..."):
        graph = build_graph()
        for chunk in graph.stream(initial, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                updates = node_output.get("status_updates", [])
                for u in updates:
                    status_lines.append(f"- {u}")
                    status_placeholder.markdown(
                        "**Progress**\n" + "\n".join(status_lines)
                    )

                report = node_output.get("final_report", "")
                if report:
                    final_report = report

    status_placeholder.markdown("**Progress**\n" + "\n".join(status_lines))

    if final_report:
        st.divider()
        st.markdown(final_report)
    else:
        st.error("No report was produced.")
