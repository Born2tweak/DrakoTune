"""Protected consent-store interface (DT-49).

The consent store is the boundary between the *automatic* rights graph and the
*human/counsel-gated* world of real consent records, contract text, and direct
identity. DT-49 defines the **interface** and a synthetic in-memory
implementation for tests; a production store backed by real consent documents,
retention obligations, and deletion authority is explicitly out of scope and
human-gated (contract §7 Out of scope; Field 15 Human-only).

Security posture (Field 18): the store keys grants by opaque ``subject_id`` and
opaque ``consent_ref`` handles. It never holds direct identity or contract text,
and :meth:`ConsentStore.shareable_grants` returns redacted records safe to share
in a pseudonymous graph.
"""

from typing import Protocol, runtime_checkable

from src.rights.grants import RightsGrant


@runtime_checkable
class ConsentStore(Protocol):
    """Read/append interface over purpose-specific rights grants.

    Implementations are append-only: :meth:`record_withdrawal` supersedes a
    grant with a withdrawn copy rather than mutating or deleting history.
    """

    def grants_for(self, subject_id: str) -> tuple[RightsGrant, ...]:
        """All *current* grants whose subject is exactly ``subject_id``."""
        ...

    def all_grants(self) -> tuple[RightsGrant, ...]:
        """Every current grant (post-withdrawal supersession)."""
        ...

    def record_withdrawal(self, subject_id: str, *, at_time: str, reason: str = "") -> tuple[RightsGrant, ...]:
        """Withdraw every current grant for ``subject_id``; return the new records."""
        ...


class InMemoryConsentStore:
    """Synthetic, identity-isolated consent store for tests and simulation.

    Holds no direct identity: only ``subject_id`` keys and opaque grant records.
    Append-only — withdrawal replaces a grant's *current* record with a withdrawn
    copy but keeps the prior record in history.
    """

    def __init__(self, grants: list[RightsGrant] | None = None) -> None:
        self._current: dict[str, RightsGrant] = {}
        self._history: list[RightsGrant] = []
        for g in grants or []:
            self.add(g)

    def add(self, grant: RightsGrant) -> None:
        if grant.grant_id in self._current:
            raise ValueError(f"duplicate grant_id {grant.grant_id!r} (grants are immutable)")
        self._current[grant.grant_id] = grant
        self._history.append(grant)

    def grants_for(self, subject_id: str) -> tuple[RightsGrant, ...]:
        return tuple(g for g in self._current.values() if g.subject_id == subject_id)

    def all_grants(self) -> tuple[RightsGrant, ...]:
        return tuple(self._current.values())

    def history(self) -> tuple[RightsGrant, ...]:
        return tuple(self._history)

    def record_withdrawal(
        self, subject_id: str, *, at_time: str, reason: str = ""
    ) -> tuple[RightsGrant, ...]:
        withdrawn: list[RightsGrant] = []
        for gid, g in list(self._current.items()):
            if g.subject_id == subject_id:
                new = g.withdrawn(at_time=at_time, reason=reason)
                self._current[gid] = new
                self._history.append(new)
                withdrawn.append(new)
        return tuple(withdrawn)

    def shareable_grants(self) -> list[dict]:
        """Redacted grant view safe to share (no ``consent_ref``/``owner``)."""
        return [g.to_dict(shareable=True) for g in self._current.values()]
