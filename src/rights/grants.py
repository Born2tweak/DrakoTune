"""Rights grant records (DT-49).

A :class:`RightsGrant` records that some *subject* (an asset ID, or a group ID
that links aliases of one person/work) is ``allowed`` / ``prohibited`` /
``conditional`` for a specific set of :class:`~src.rights.purposes.Purpose`
values, optionally until an expiry, optionally subject to named conditions.

Grants are immutable frozen records. A withdrawal is a *new* record
(``status = withdrawn`` via a correction/event), never a mutation of the
original — the same append-only discipline DT-46 uses for provenance.

Direct identity and contract text never live on the grant. The grant carries
only an opaque ``consent_ref`` handle into a protected store; resolving that
handle to a real person/contract is a human/counsel-gated step outside DT-49.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.canonical import content_hash
from src.evaluation.semantics.enums import (
    GrantStatus,
    RightsPermission,
    parse_enum,
)
from src.rights.purposes import Purpose

GRANT_SCHEMA = "drakotune.rights_grant"
GRANT_SCHEMA_VERSION = "1.0.0"

# Permissions a *stored grant* may declare. Resolved/derived states such as
# ``unknown``/``expired``/``withdrawn`` are produced by authorization, never
# authored directly on an active grant.
_DECLARABLE_PERMISSIONS = frozenset(
    {RightsPermission.ALLOWED, RightsPermission.PROHIBITED, RightsPermission.CONDITIONAL}
)


@dataclass(frozen=True)
class RightsGrant:
    """One purpose-specific rights grant over a subject."""

    grant_id: str
    subject_id: str
    purposes: tuple[Purpose, ...]
    permission: RightsPermission
    granted_at: str
    status: GrantStatus = GrantStatus.ACTIVE
    expires_at: str | None = None
    conditions: tuple[str, ...] = ()
    consent_ref: str | None = None  # opaque; never direct identity or contract text
    owner: str = "rights_owner"
    schema: str = GRANT_SCHEMA
    schema_version: str = GRANT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.permission not in _DECLARABLE_PERMISSIONS:
            raise ValueError(
                f"a stored grant may only declare {sorted(p.value for p in _DECLARABLE_PERMISSIONS)}; "
                f"got {self.permission.value!r} (unknown/expired/withdrawn are resolved states)"
            )
        if self.permission is RightsPermission.CONDITIONAL and not self.conditions:
            raise ValueError("a conditional grant must list at least one condition")

    def covers(self, purpose: Purpose) -> bool:
        return purpose in self.purposes

    def is_expired_at(self, at_time: str) -> bool:
        """True if this grant has passed its expiry at ``at_time`` (ISO strings).

        Timestamps are compared as ISO-8601 strings, which sort chronologically
        when zero-padded — the same lexical-time assumption the rest of the
        provenance layer uses.
        """
        return self.expires_at is not None and at_time >= self.expires_at

    def to_dict(self, *, with_hash: bool = True, shareable: bool = False) -> dict:
        """Serialize.

        ``shareable=True`` redacts the opaque ``consent_ref`` and ``owner`` so a
        pseudonymous grant record can be shared without leaking the handle that
        links to a protected consent record (DT-49 Field 18).
        """
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "subject_id": self.subject_id,
            "purposes": [p.value for p in self.purposes],
            "permission": self.permission.value,
            "granted_at": self.granted_at,
            "status": self.status.value,
            "expires_at": self.expires_at,
            "conditions": list(self.conditions),
            "consent_ref": None if shareable else self.consent_ref,
            "owner": "redacted" if shareable else self.owner,
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "RightsGrant":
        return cls(
            grant_id=d["grant_id"],
            subject_id=d["subject_id"],
            purposes=tuple(parse_enum(Purpose, p) for p in d["purposes"]),
            permission=parse_enum(RightsPermission, d["permission"]),
            granted_at=d["granted_at"],
            status=parse_enum(GrantStatus, d.get("status", "active")),
            expires_at=d.get("expires_at"),
            conditions=tuple(d.get("conditions", ())),
            consent_ref=d.get("consent_ref"),
            owner=d.get("owner", "rights_owner"),
            schema=d.get("schema", GRANT_SCHEMA),
            schema_version=d.get("schema_version", GRANT_SCHEMA_VERSION),
        )

    def withdrawn(self, *, at_time: str, reason: str = "") -> "RightsGrant":
        """Return a new grant record marked withdrawn (original is untouched)."""
        return RightsGrant(
            grant_id=self.grant_id,
            subject_id=self.subject_id,
            purposes=self.purposes,
            permission=self.permission,
            granted_at=self.granted_at,
            status=GrantStatus.WITHDRAWN,
            expires_at=self.expires_at,
            conditions=self.conditions + ((f"withdrawn:{reason}",) if reason else ()),
            consent_ref=self.consent_ref,
            owner=self.owner,
        )
