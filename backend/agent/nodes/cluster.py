"""decide_cluster + cluster nodes.

Phase 3: ``decide_cluster`` (pure logic, no LLM) chooses a clustering strategy
by class count; ``cluster`` is stubbed to set ``effective_class_list = class_list``.
Phase 4: implement ``cluster`` with LLM meta-class generation, cached by
``class_list_hash`` — hierarchical_d1 (10-25 classes), hierarchical_d2 (26+).
See ARCHITECTURE.md §2.3.
"""
