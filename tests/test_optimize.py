import importlib
import logging
from pathlib import Path

import pytest


def test_missing_state(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)

    def always_false(self):
        return False

    monkeypatch.setattr(Path, "exists", always_false)
    with pytest.raises(SystemExit):
        importlib.reload(importlib.import_module("trading_intel.optimize"))
    assert "LSTM state not found" in caplog.text
