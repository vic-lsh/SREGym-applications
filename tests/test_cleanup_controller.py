"""The optional controller is source-owned and cleans up through the API."""
import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1] / "hotelReservation/optional/cleanup-controller"


def load_controller():
    spec = importlib.util.spec_from_file_location("cleanup_controller", ROOT / "controller.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_controller_only_removes_its_finalizer_and_records_completion():
    controller = load_controller()
    calls = []

    def api(path, method="GET", body=None):
        calls.append((path, method, body))
        if method == "GET":
            return {"metadata": {"resourceVersion": "12", "deletionTimestamp": "now",
                                 "finalizers": [controller.FINALIZER, "other/owner"]}}
        return {}

    assert controller.reconcile(api, "hotel-reservation")
    assert calls[1][2] == {"metadata": {"resourceVersion": "12", "finalizers": ["other/owner"]}}
    assert controller.COMPLETION in calls[2][2]["metadata"]["annotations"]


def test_forbidden_cannot_claim_completion():
    controller = load_controller()
    calls = []

    def api(path, method="GET", body=None):
        calls.append(method)
        if method == "GET":
            return {"metadata": {"resourceVersion": "1", "deletionTimestamp": "now",
                                 "finalizers": [controller.FINALIZER]}}
        raise HTTPError(path, 403, "Forbidden", {}, None)

    try:
        controller.reconcile(api, "hotel-reservation")
    except HTTPError as exc:
        assert exc.code == 403
    else:
        raise AssertionError("403 must remain observable")
    assert calls == ["GET", "PATCH"]


def test_idle_controller_does_not_write():
    controller = load_controller()
    assert not controller.reconcile(lambda *args: {"metadata": {}}, "hotel-reservation")


def test_manifest_contains_only_source_objects():
    objects = json.loads((ROOT / "resources.json").read_text())["items"]
    assert {o["kind"] for o in objects} == {
        "ServiceAccount", "ClusterRole", "ClusterRoleBinding", "Deployment"}
    assert all("platform.io/injected" not in o["metadata"].get("labels", {}) for o in objects)
    deployment = next(o for o in objects if o["kind"] == "Deployment")
    assert deployment["spec"]["template"]["spec"]["serviceAccountName"] == "cleanup-controller"


def test_optional_component_materializes_as_plain_source_manifests(tmp_path):
    import shutil
    import runpy
    source = tmp_path / 'hotel'
    shutil.copytree(ROOT, source / 'optional/cleanup-controller')
    (source/'kubernetes').mkdir()
    enable = runpy.run_path(str(ROOT/'enable.py'))['enable']
    target = enable(source, 'hotel-lane')
    objects = [json.loads(document) for document in target.read_text().split('\n---\n')]
    assert len(objects) == 5
    assert all(obj['metadata'].get('namespace') == 'hotel-lane'
               for obj in objects if obj['kind'] not in {'ClusterRole', 'ClusterRoleBinding'})
    assert next(obj for obj in objects if obj['kind'] == 'ClusterRoleBinding')['subjects'][0]['namespace'] == 'hotel-lane'
