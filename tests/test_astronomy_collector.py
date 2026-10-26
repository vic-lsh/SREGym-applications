"""Collector parallelism is an app-owned source policy, independent of host cores."""

from pathlib import Path
import yaml


def test_collector_runtime_parallelism_is_bounded_without_resource_changes():
    values = yaml.safe_load((Path(__file__).resolve().parents[1] / "astronomy-shop-overrides.yaml").read_text())
    collector = values["opentelemetry-collector"]
    assert collector["extraEnvs"] == [{"name": "GOMAXPROCS", "value": "2"}]
    assert collector["presets"]["hostMetrics"]["enabled"] is False
    assert "resources" not in collector
