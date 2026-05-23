from __future__ import annotations

import sys

import pytest

from lean_hybrid_reasoner.cli import make_proposer_named, make_repairer_named
from lean_hybrid_reasoner.dspy_modules.dspy_tactics import DSPyUnavailable
from lean_hybrid_reasoner.dspy_modules.heuristic_tactics import (
    HeuristicTacticProposer,
    HeuristicTacticRepairer,
)


def test_make_proposer_named_falls_back_to_heuristic_when_configured(monkeypatch):
    monkeypatch.setenv("LHR_DSPY_FALLBACK", "heuristic")
    monkeypatch.setitem(sys.modules, "dspy", None)

    proposer = make_proposer_named("dspy")
    assert isinstance(proposer, HeuristicTacticProposer)


def test_make_repairer_named_falls_back_to_heuristic_when_configured(monkeypatch):
    monkeypatch.setenv("LHR_DSPY_FALLBACK", "heuristic")
    monkeypatch.setitem(sys.modules, "dspy", None)

    repairer = make_repairer_named("dspy")
    assert isinstance(repairer, HeuristicTacticRepairer)


def test_make_proposer_named_raises_when_fallback_not_heuristic(monkeypatch):
    monkeypatch.setenv("LHR_DSPY_FALLBACK", "none")
    monkeypatch.setitem(sys.modules, "dspy", None)

    with pytest.raises(DSPyUnavailable):
        make_proposer_named("dspy")
