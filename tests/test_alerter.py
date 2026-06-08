"""Alert engine tests."""
import pytest
from scheduler.alerter import check_mode_1, check_mode_2


def test_mode_1_triggers_below_target():
    assert check_mode_1(85.0, 100.0) is True


def test_mode_1_triggers_at_target():
    assert check_mode_1(100.0, 100.0) is True


def test_mode_1_no_trigger_above_target():
    assert check_mode_1(105.0, 100.0) is False


def test_mode_1_no_trigger_without_target():
    assert check_mode_1(50.0, None) is False


def test_mode_2_triggers_on_drop():
    assert check_mode_2(85.0, 100.0, 10.0) is True


def test_mode_2_triggers_on_gain():
    assert check_mode_2(115.0, 100.0, 10.0) is True


def test_mode_2_no_trigger_in_threshold():
    assert check_mode_2(105.0, 100.0, 10.0) is False


def test_mode_2_no_trigger_without_cost():
    assert check_mode_2(85.0, None, 10.0) is False
