from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.experiments.replay import replay_proof


def test_replay_validates_recorded_mock_proof():
    payload = replay_proof(
        MockLeanBackend(),
        "and_comm_example",
        ["intro h", "exact And.intro h.right h.left"],
    )
    assert payload["valid"] is True
    assert payload["solved"] is True
    assert payload["failed_step"] is None


def test_replay_reports_invalid_tactic():
    payload = replay_proof(MockLeanBackend(), "and_comm_example", ["bad_tactic"])
    assert payload["valid"] is False
    assert payload["failed_step"] == 1


class VerifyingMockBackend(MockLeanBackend):
    def verify_proof(self, theorem_name: str, proof: list[str]) -> dict[str, object]:
        return {
            "verified": theorem_name == "and_comm_example" and bool(proof),
            "returncode": 0,
        }


def test_replay_verify_uses_backend_verifier():
    payload = replay_proof(
        VerifyingMockBackend(),
        "and_comm_example",
        ["intro h", "exact And.intro h.right h.left"],
        verify_with_lean=True,
    )
    assert payload["valid"] is True
    assert payload["solved"] is True
    assert payload["verification"]["verified"] is True
