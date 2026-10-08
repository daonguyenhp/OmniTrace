import os
from src.config import Settings, get_settings
from pytest import MonkeyPatch

def test_settings_default_values():
    settings = Settings()
    assert settings.service_name == "omnitrace"
    assert settings.record_prompt == True
    assert settings.oracle_budget == 50

def test_settings_from_env():

    monkeypatch = MonkeyPatch()

    monkeypatch.setenv("SERVICE_NAME", "omnitrace-agent")
    monkeypatch.setenv("RECORD_PROMPT", "false")
    monkeypatch.setenv("ORACLE_BUDGET", "100")

    settings = get_settings()
    assert settings.service_name == "omnitrace-agent"
    assert settings.record_prompt == False
    assert settings.oracle_budget == 100