from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend


def test_mock_backend_solves_add_zero_with_simp():
    backend = MockLeanBackend()
    state = backend.load_theorem("add_zero_example")
    result = backend.execute_tactic(state, "simp")
    assert result.accepted is True
    assert result.solved is True


def test_mock_backend_and_comm_two_steps():
    backend = MockLeanBackend()
    state = backend.load_theorem("and_comm_example")
    first = backend.execute_tactic(state, "intro h")
    assert first.accepted is True
    assert first.solved is False
    state.current_goal = first.new_goals[0]
    state.open_goals = first.new_goals
    state.hypotheses = first.new_hypotheses
    state.proof_prefix.append("intro h")
    second = backend.execute_tactic(state, "exact And.intro h.right h.left")
    assert second.accepted is True
    assert second.solved is True
