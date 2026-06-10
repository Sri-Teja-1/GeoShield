"""synthesize node.

Phase 3: passthrough when there is a single patch; otherwise call the LLM with
a positional synthesis prompt to merge per-patch descriptions into one unified
image description. See ARCHITECTURE.md §2.5.
"""
