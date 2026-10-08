"""P14-F Research-Only Feature Registry (public package)."""
from .registry import (
    FeatureSetBindingError,
    MemberUnresolvedError,
    RegistryIntegrityError,
    feature_set_id,
    load_registry,
    registry_sha256,
    resolve_membership,
    verify_against_frozen,
)

__all__ = [
    "FeatureSetBindingError",
    "MemberUnresolvedError",
    "RegistryIntegrityError",
    "feature_set_id",
    "load_registry",
    "registry_sha256",
    "resolve_membership",
    "verify_against_frozen",
]
