import hashlib
import json
from pathlib import Path
from typing import Any


class EvidenceStoreError(RuntimeError):
    pass


class EvidenceStore:
    def __init__(
        self,
        customers: list[dict[str, Any]],
        orders: list[dict[str, Any]],
        policy: dict[str, Any] | None,
    ) -> None:
        self._customers = self._index(customers, "customer_id", "customer")
        self._orders = self._index(orders, "order_id", "order")
        self._policy = policy

    @classmethod
    def from_directory(cls, directory: Path | None = None) -> "EvidenceStore":
        data_directory = directory or Path(__file__).resolve().parents[2] / "data"
        try:
            customers = json.loads((data_directory / "customers.json").read_text(encoding="utf-8"))
            orders = json.loads((data_directory / "orders.json").read_text(encoding="utf-8"))
            policy = json.loads((data_directory / "refund_policy.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise EvidenceStoreError("Trusted evidence fixtures could not be loaded") from error

        if not isinstance(customers, list) or not isinstance(orders, list) or not isinstance(policy, dict):
            raise EvidenceStoreError("Trusted evidence fixtures have an invalid top-level shape")
        return cls(customers, orders, policy)

    @staticmethod
    def _index(
        records: list[dict[str, Any]],
        id_field: str,
        label: str,
    ) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get(id_field), str):
                raise EvidenceStoreError(f"Trusted {label} fixture is missing {id_field}")
            record_id = record[id_field]
            if record_id in indexed:
                raise EvidenceStoreError(f"Duplicate trusted {label} record: {record_id}")
            indexed[record_id] = record
        return indexed

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        return self._customers.get(customer_id)

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        return self._orders.get(order_id)

    def get_policy(self) -> dict[str, Any] | None:
        return self._policy

    @staticmethod
    def snapshots(
        order: dict[str, Any],
        customer: dict[str, Any],
        policy: dict[str, Any],
        retrieved_at: str,
    ) -> list[dict[str, Any]]:
        sources = (
            ("ORDER", order["order_id"], order.get("version"), order),
            ("CUSTOMER", customer["customer_id"], "unversioned", customer),
            ("POLICY", policy["policy_id"], policy.get("version"), policy),
        )
        evidence: list[dict[str, Any]] = []
        for source_type, source_id, version, record in sources:
            digest = hashlib.sha256(
                json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            ).hexdigest()
            evidence.append(
                {
                    "evidence_id": f"ev_{source_type}_{source_id}",
                    "source_type": source_type,
                    "source_id": source_id,
                    "version": version,
                    "retrieved_at": retrieved_at,
                    "digest": digest,
                }
            )
        return evidence
