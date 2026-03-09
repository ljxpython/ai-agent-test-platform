from __future__ import annotations

from app.api.langgraph import router as langgraph_router
from app.api.management import router as management_router
from app.bootstrap.lifespan import lifespan
from app.config import load_settings
from app.logging_setup import setup_backend_logging
from app.middleware.audit_log import register_audit_log_middleware
from app.middleware.auth_context import register_auth_context_middleware
from app.middleware.request_context import register_request_context_middleware
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    load_dotenv()
    settings = load_settings()
    setup_backend_logging(settings)

    app = FastAPI(
        title="LangGraph Transparent Proxy",
        version="0.1.0",
        docs_url="/docs" if settings.api_docs_enabled else None,
        redoc_url="/redoc" if settings.api_docs_enabled else None,
        openapi_url="/openapi.json" if settings.api_docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.include_router(management_router)
    app.include_router(langgraph_router)
    # Retired after frontend verification; keep implementation files for reference only.
    # app.include_router(frontend_passthrough_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.proxy_cors_allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_auth_context_middleware(app, settings)
    register_audit_log_middleware(app, settings)
    register_request_context_middleware(app)

    @app.get("/_proxy/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Retired after frontend verification; keep implementation files for reference only.
    # @app.api_route(
    #     "/_runtime/{full_path:path}",
    #     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    # )
    # async def runtime_passthrough(request: Request, full_path: str) -> Response:
    #     return await passthrough_request(request=request, full_path=full_path, settings=settings, logger=logger)

    # @app.api_route(
    #     "/{full_path:path}",
    #     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    # )
    # async def passthrough(request: Request, full_path: str) -> Response:
    #     return await passthrough_request(request=request, full_path=full_path, settings=settings, logger=logger)

    return app
