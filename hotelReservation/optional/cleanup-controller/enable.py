"""Materialize the optional component into the plain-manifest hotel installation."""

import argparse
import json
from pathlib import Path


def manifests(component: Path, namespace: str) -> list[dict]:
    objects = json.loads((component / "resources.json").read_text())["items"]
    objects.append(
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "cleanup-controller-script"},
            "data": {"controller.py": (component / "controller.py").read_text()},
        }
    )
    for obj in objects:
        if obj["kind"] not in {"ClusterRole", "ClusterRoleBinding"}:
            obj["metadata"]["namespace"] = namespace
        if obj["kind"] == "ClusterRoleBinding":
            for subject in obj["subjects"]:
                subject["namespace"] = namespace
    return objects


def enable(source: Path, namespace: str = "hotel-reservation") -> Path:
    """Call before the application workspace's initial Git snapshot."""
    component = source / "optional/cleanup-controller"
    target = source / "kubernetes/cleanup-controller.yaml"
    target.write_text("\n---\n".join(json.dumps(obj, indent=2) for obj in manifests(component, namespace)) + "\n")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", default="hotel-reservation")
    args = parser.parse_args()
    enable(Path(__file__).resolve().parents[2], args.namespace)
