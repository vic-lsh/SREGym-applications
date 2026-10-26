# Reservation cleanup controller (optional)

Include this Kustomize directory in a hotel overlay and set that overlay's namespace
(the normal namespace is `hotel-reservation`). It installs the controller, script,
ServiceAccount and cluster RBAC as application source. It creates no cleanup token.
The root `kubernetes/` installation remains unchanged.

The controller uses its Pod identity to remove only its own finalizer from a deleting
`reservation-cleanup-token` ConfigMap and records completion on its Deployment.
Other finalizers and annotations are preserved. API denials are real controller logs;
the benchmark does not perform reconciliation on its behalf.

The `python:3.12-alpine` image must be available in the lane before injection.
Run offline checks with `python -m pytest tests/test_cleanup_controller.py`.

For a plain-manifest installation, run `python optional/cleanup-controller/enable.py`
from the hotel root **before** taking the application's initial Git snapshot. This
writes all five objects to `kubernetes/cleanup-controller.yaml`; commit that file
as application source. Set `--namespace` for a lane using a different namespace.
SREGym's `SREGYM_HOTEL_CLEANUP_CONTROLLER=1` workspace flag performs this activation
before its initial snapshot. Existing seeded workspaces are copied unchanged and
must already contain the enabled component.
