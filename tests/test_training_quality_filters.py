import pytest

from lean_hybrid_reasoner.training.quality_filters import apply_quality_filter


def test_apply_quality_filter_accepted():
    examples = [
        {"accepted": True, "solved": False},
        {"accepted": False, "solved": False},
        {"accepted": True, "solved": True},
    ]
    filtered, summary = apply_quality_filter(examples, min_quality="accepted")
    assert len(filtered) == 2
    assert summary["dropped"] == 1


def test_apply_quality_filter_solved():
    examples = [
        {"accepted": True, "solved": False},
        {"accepted": True, "solved": True},
    ]
    filtered, summary = apply_quality_filter(examples, min_quality="solved")
    assert len(filtered) == 1
    assert summary["kept"] == 1


def test_apply_quality_filter_invalid_level():
    with pytest.raises(ValueError):
        apply_quality_filter([], min_quality="excellent")
