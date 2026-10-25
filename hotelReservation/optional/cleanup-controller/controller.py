"""Reconcile the reservation cleanup token with the controller's own API identity."""

import json
import os
import ssl
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

FINALIZER = "cleanup.reservations.io/pending-cleanup"
COMPLETION = "cleanup-controller.platform.io/finalizer-cleanup-completed"
TOKEN = "reservation-cleanup-token"


def reconcile(api, namespace: str) -> bool:
    """Remove only our finalizer, then record independently observable completion."""
    path = f"/api/v1/namespaces/{namespace}/configmaps/{TOKEN}"
    try:
        token = api(path)
    except HTTPError as exc:
        if exc.code == 404:
            return False
        raise
    metadata = token["metadata"]
    finalizers = metadata.get("finalizers", [])
    if not metadata.get("deletionTimestamp") or FINALIZER not in finalizers:
        return False
    api(
        path,
        "PATCH",
        {
            "metadata": {
                "resourceVersion": metadata["resourceVersion"],
                "finalizers": [value for value in finalizers if value != FINALIZER],
            }
        },
    )
    api(
        f"/apis/apps/v1/namespaces/{namespace}/deployments/cleanup-controller",
        "PATCH",
        {"metadata": {"annotations": {COMPLETION: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}},
    )
    return True


def main() -> None:
    namespace = os.environ["POD_NAMESPACE"]
    credentials = Path("/var/run/secrets/kubernetes.io/serviceaccount")
    context = ssl.create_default_context(cafile=str(credentials / "ca.crt"))
    endpoint = "https://kubernetes.default.svc"

    def api(path, method="GET", body=None):
        # Re-read the projected token to support Kubernetes token rotation.
        request = Request(
            endpoint + path,
            method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Authorization": "Bearer " + (credentials / "token").read_text().strip(),
                "Content-Type": "application/merge-patch+json",
            },
        )
        with urlopen(request, context=context, timeout=10) as response:
            return json.load(response)

    while True:
        try:
            if reconcile(api, namespace):
                print("cleanup-controller completed finalizer cleanup", flush=True)
        except HTTPError as exc:
            if exc.code == 403:
                print("Kubernetes API denied the finalizer cleanup request with Forbidden", flush=True)
            else:
                print(f"cleanup-controller API status {exc.code}", flush=True)
        except (OSError, ValueError, KeyError) as exc:
            print(f"cleanup-controller reconcile error: {type(exc).__name__}", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
