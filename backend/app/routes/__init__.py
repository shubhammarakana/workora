from .auth import router as auth_router
from .shipments import router as shipments_router
from .tickets import router as tickets_router
from .invoices import router as invoices_router
from .chat import router as chat_router
from .customer_service import router as customer_service_router
from .delivery import router as delivery_router
from .billing import router as billing_router
from .approval import router as approval_router
from .ai_manager import router as ai_manager_router

__all__ = [
    "auth_router",
    "shipments_router",
    "tickets_router",
    "invoices_router",
    "chat_router",
    "customer_service_router",
    "delivery_router",
    "billing_router",
    "approval_router",
    "ai_manager_router"
]


