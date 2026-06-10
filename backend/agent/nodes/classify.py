"""classify node.

Phase 3: build a structured prompt with retrieved context, call Gemini in JSON
mode, and validate the predicted class is within ``effective_class_list``.
Produces ``predicted_class``, ``confidence``, ``reasoning``,
``alternative_classes``, ``ambiguity_reason``. See ARCHITECTURE.md §2.7.
"""
