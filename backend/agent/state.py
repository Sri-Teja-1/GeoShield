"""Agent state schema.

Phase 2: implement ``AgentState`` as a flat ``TypedDict`` with every field from
ARCHITECTURE.md §4.2. ``patch_descriptions`` and ``pipeline_errors`` use
``Annotated[List[str], operator.add]`` reducers for parallel-safe appending
(the ``describe_patches`` fan-out writes concurrently). Downstream nodes always
read ``effective_class_list``, never ``class_list`` directly.
"""
