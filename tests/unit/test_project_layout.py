import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "agent_platform.common",
        "agent_platform.infra",
        "agent_platform.evaluation",
        "agent_platform.agents",
        "agent_platform.agents.incident_agent",
        "agent_platform.app",
    ],
)
def test_layer_package_is_importable(module: str) -> None:
    assert importlib.import_module(module).__doc__
