from lean_hybrid_reasoner.search.tactic_memory import TacticMemory


def test_tactic_memory_suppresses_after_threshold():
    memory = TacticMemory(failure_threshold=2)
    state_key = "theorem::goal::hyps"
    tactic = "simp"

    assert memory.should_suppress(state_key, tactic) is False
    memory.record_failure(state_key, tactic)
    assert memory.should_suppress(state_key, tactic) is False
    memory.record_failure(state_key, tactic)
    assert memory.should_suppress(state_key, tactic) is True


def test_tactic_memory_records_success_best_tactics():
    memory = TacticMemory()
    state_key = "theorem::goal::hyps"
    memory.record_success(state_key, "intro h")
    assert memory.should_suppress(state_key, "intro h") is False
