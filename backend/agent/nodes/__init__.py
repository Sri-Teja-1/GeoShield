"""LangGraph node implementations.

Each node is ``async def node_name(state: AgentState) -> dict`` returning a
partial state update. Node-level failures are non-fatal: log to
``pipeline_errors`` and continue where possible (CLAUDE.md §12 rule 5).
"""
