"""External tools for the coordinator agent.

Ticket lookup is ``McpIncidentLookup`` in ``mcp_incidents.py``. Inventory stays
a direct read of the inventory API.
"""

from .contracts import (
    InventoryLookupInput,
    InventoryLookupOutput,
    ProductStock,
    TicketLookupInput,
    TicketLookupOutput,
    TicketRecord,
    ToolStatus,
)
from .inventory import InventoryLookupTool
from .session import (
    TOOL_TIMEOUT_SECONDS,
    ReadOnlyApiSession,
    ReadOnlyViolation,
    ServiceCredentials,
)

__all__ = [
    "TOOL_TIMEOUT_SECONDS",
    "InventoryLookupInput",
    "InventoryLookupOutput",
    "InventoryLookupTool",
    "ProductStock",
    "ReadOnlyApiSession",
    "ReadOnlyViolation",
    "ServiceCredentials",
    "TicketLookupInput",
    "TicketLookupOutput",
    "TicketRecord",
    "ToolStatus",
]
