from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import engine, Base
from .routes import (
    auth_router,
    shipments_router,
    tickets_router,
    invoices_router,
    chat_router,
    customer_service_router,
    delivery_router,
    billing_router,
    approval_router,
    ai_manager_router
)

# Ensure database tables exist on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LogiFlow Logistics API",
    description="Backend REST API for LogiFlow Customer Chatbot — Powered by Workora AI Employee",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handlers for Clean JSON Errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "code": f"HTTP_{exc.status_code}"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )

# Health Check Route
@app.get("/health", tags=["Health"], summary="API Health Check")
def health_check():
    return {
        "status": "ok",
        "service": "LogiFlow Logistics API"
    }

# Register API Routers
app.include_router(auth_router)
app.include_router(shipments_router)
app.include_router(tickets_router)
app.include_router(invoices_router)
app.include_router(chat_router)
app.include_router(customer_service_router)
app.include_router(delivery_router)
app.include_router(billing_router)
app.include_router(approval_router)
app.include_router(ai_manager_router)

# Serve Frontend static files (index.html)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(os.path.join(root_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

