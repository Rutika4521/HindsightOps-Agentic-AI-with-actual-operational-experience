"""
Hindsight Client Abstraction
All Hindsight API interactions are isolated in this module.

Correct SDK method names (verified against hindsight-client==0.10.1):
  - retain:         client.aretain(...)
  - recall:         client.arecall(...)
  - list memories:  client.memory.list_memories(...)       # NOT list_memory_units
  - clear memories: client.memory.clear_bank_memories(...) # NOT clear_memory
  - bank stats:     client.banks.get_agent_stats(...)      # returns BankStatsResponse
  - health:         client.aget_version()
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

from hindsight_client import Hindsight

logger = logging.getLogger(__name__)


class HindsightMemoryClient:
    """
    Dedicated abstraction layer for Hindsight memory operations.

    All Hindsight SDK calls go through this class — nowhere else.
    """

    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "incident-memory-commander")

        if not self.base_url:
            raise ValueError("HINDSIGHT_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("HINDSIGHT_API_KEY environment variable is required")

        self._client = Hindsight(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=120.0,
            user_agent="incident-memory-commander/1.0.0",
        )
        logger.info(f"HindsightMemoryClient initialized: bank_id={self.bank_id}")

    # ── Retain ────────────────────────────────────────────────────────────────

    async def retain_incident_memory(
        self,
        content: str,
        incident_id: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Store a resolved incident experience into Hindsight memory.
        """
        try:
            all_tags = [f"incident:{incident_id}"] + (tags or [])
            all_metadata = {"incident_id": incident_id, **(metadata or {})}

            response = await self._client.aretain(
                bank_id=self.bank_id,
                content=content,
                document_id=f"incident-{incident_id}",
                tags=all_tags,
                metadata=all_metadata,
                context=f"Production incident experience: {incident_id}",
            )

            items_count = getattr(response, "items_count", 0)
            logger.info(
                f"Retained incident memory: incident_id={incident_id}, items={items_count}"
            )
            return {
                "success": True,
                "incident_id": incident_id,
                "items_count": items_count,
            }

        except Exception as e:
            logger.error(f"Failed to retain incident memory: {e}", exc_info=True)
            return {"success": False, "error": str(e), "incident_id": incident_id}

    # ── Recall ────────────────────────────────────────────────────────────────

    async def recall_relevant_incidents(
        self,
        query: str,
        tags: Optional[list[str]] = None,
        max_tokens: int = 6000,
    ) -> dict[str, Any]:
        """
        Recall relevant historical incident experiences from Hindsight.
        """
        try:
            response = await self._client.arecall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=max_tokens,
                budget="mid",
                tags=tags,
                tags_match="any",
            )

            # arecall returns RecallResponse where .results is a list of
            # RecallResult objects each having a .text attribute (plain string).
            # We join them all into one block of text for the LLM.
            raw_results = getattr(response, "results", None)
            if isinstance(raw_results, list):
                # Each item is a RecallResult with a .text field
                results_text = "\n\n".join(
                    getattr(r, "text", str(r)) for r in raw_results if getattr(r, "text", None)
                )
            elif isinstance(raw_results, str):
                results_text = raw_results
            elif hasattr(response, "to_prompt_string"):
                results_text = response.to_prompt_string() or ""
            else:
                results_text = ""

            logger.info(
                f"Recalled memories: results_count={len(raw_results) if isinstance(raw_results, list) else 'n/a'}, "
                f"text_len={len(results_text)}"
            )

            return {
                "success": True,
                "results": results_text,
                "has_memories": bool(results_text and results_text.strip()),
            }

        except Exception as e:
            logger.error(f"Failed to recall incident memories: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "results": "",
                "has_memories": False,
            }

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_all_memories(self, limit: int = 100) -> dict[str, Any]:
        """
        List all stored memories for the Memory Explorer UI.
        SDK method: memory.list_memories (returns ListMemoryUnitsResponse)
        """
        try:
            response = await self._client.memory.list_memories(
                bank_id=self.bank_id,
                limit=limit,
                _request_timeout=60.0,
            )
            items = getattr(response, "items", []) or []
            total = getattr(response, "total", len(items))
            return {
                "success": True,
                "memories": [self._serialize_memory_item(item) for item in items],
                "total": total,
            }
        except Exception as e:
            logger.error(f"Failed to list memories: {e}", exc_info=True)
            return {"success": False, "error": str(e), "memories": [], "total": 0}

    # ── Clear ─────────────────────────────────────────────────────────────────

    async def clear_all_memories(self) -> dict[str, Any]:
        """
        Clear all memories from the bank (demo reset).
        SDK method: memory.clear_bank_memories (NOT clear_memory)
        """
        try:
            await self._client.memory.clear_bank_memories(
                bank_id=self.bank_id,
                _request_timeout=120.0,
            )
            logger.info(f"Cleared all memories from bank: {self.bank_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ── Stats ─────────────────────────────────────────────────────────────────

    async def get_bank_stats(self) -> dict[str, Any]:
        """
        Get memory bank statistics.
        SDK method: banks.get_agent_stats (returns BankStatsResponse)
        Fields: bank_id, total_nodes, total_documents, total_observations, etc.
        """
        try:
            response = await self._client.banks.get_agent_stats(
                bank_id=self.bank_id,
                _request_timeout=30.0,
            )
            return {
                "success": True,
                "bank_id": self.bank_id,
                "stats": {
                    "bank_id": self.bank_id,
                    "total_nodes": getattr(response, "total_nodes", 0),
                    "total_documents": getattr(response, "total_documents", 0),
                    "total_observations": getattr(response, "total_observations", 0),
                    "last_memory_write_at": str(getattr(response, "last_memory_write_at", "") or ""),
                    "pending_operations": getattr(response, "pending_operations", 0),
                    # Alias fields to match UI expectations
                    "memory_count": getattr(response, "total_nodes", 0),
                    "document_count": getattr(response, "total_documents", 0),
                    "entity_count": getattr(response, "total_observations", 0),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get bank stats: {e}", exc_info=True)
            return {"success": False, "error": str(e), "bank_id": self.bank_id}

    # ── Health ────────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Check if Hindsight is reachable."""
        try:
            version = await self._client.aget_version()
            return {
                "success": True,
                "api_version": getattr(version, "api_version", "unknown"),
                "bank_id": self.bank_id,
            }
        except Exception as e:
            logger.error(f"Hindsight health check failed: {e}")
            return {"success": False, "error": str(e)}

    async def ensure_bank_exists(self) -> dict[str, Any]:
        """
        Ensure the memory bank exists, creating it if needed.
        Uses create_or_update_bank which is idempotent — safe to call every startup.
        """
        try:
            from hindsight_client_api.models.create_bank_request import CreateBankRequest
            request = CreateBankRequest(
                name="Incident Memory Commander",
                mission=(
                    "Store and recall production incident experiences for an SRE team. "
                    "Remember: symptoms, metrics, root causes, actions that failed, "
                    "actions that succeeded, and lessons learned from every incident."
                ),
                background=(
                    "This bank contains resolved production incident experiences. "
                    "Each memory describes a real incident: what happened, what was tried, "
                    "what failed, what worked, and what was learned."
                ),
                enable_observations=True,
                enable_text_search=True,
                enable_temporal_retrieval=True,
                enable_graph_retrieval=True,
            )
            await self._client.banks.create_or_update_bank(
                bank_id=self.bank_id,
                create_bank_request=request,
                _request_timeout=30.0,
            )
            logger.info(f"Memory bank ready: {self.bank_id}")
            return {"success": True, "bank_id": self.bank_id}
        except Exception as e:
            logger.warning(f"ensure_bank_exists (bank may already exist): {e}")
            return {"success": False, "error": str(e)}

    # ── Serialization ─────────────────────────────────────────────────────────

    def _serialize_memory_item(self, item: Any) -> dict:
        """
        Convert a Hindsight MemoryItem to a serializable dict.
        MemoryItem fields: content, timestamp, context, metadata, document_id,
                          entities, tags, observation_scopes, strategy, update_mode
        """
        try:
            tags = getattr(item, "tags", None) or []
            metadata = getattr(item, "metadata", None) or {}
            doc_id = getattr(item, "document_id", "") or ""
            content = getattr(item, "content", "") or ""
            timestamp = getattr(item, "timestamp", None)

            # Extract incident_id from tags or metadata
            incident_id = metadata.get("incident_id", "")
            if not incident_id:
                for tag in tags:
                    if tag.startswith("incident:"):
                        incident_id = tag.split(":", 1)[1]
                        break

            return {
                "id": doc_id or incident_id or "unknown",
                "incident_id": incident_id,
                "content": str(content),
                "created_at": str(timestamp) if timestamp else "",
                "tags": list(tags),
                "metadata": dict(metadata),
                "document_id": str(doc_id),
                "context": str(getattr(item, "context", "") or ""),
            }
        except Exception as ex:
            logger.warning(f"Failed to serialize memory item: {ex}")
            return {
                "id": "unknown", "incident_id": "", "content": str(item),
                "created_at": "", "tags": [], "metadata": {}, "document_id": "", "context": "",
            }

    async def close(self):
        """Clean up client resources."""
        await self._client.aclose()
