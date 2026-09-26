# Disable Guardrails Hub telemetry BEFORE Guard/validator imports.
# Do NOT set OTEL_SDK_DISABLED globally — that also disables Langfuse.
try:
    from guardrails.classes.rc import RC
    from guardrails.settings import settings as guardrails_settings

    guardrails_settings.disable_tracing = True
    guardrails_settings.rc = RC(
        enable_metrics=False,
        use_remote_inferencing=False,
    )
except Exception:  # noqa: BLE001
    # Guardrails is optional at import time; ignore missing/broken hub config.
    pass  # noqa: S110

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.controller.ai_controller import router as ai_router

_REQUEST_EXAMPLE = {
    "text": "I love this product! The quality is outstanding.",
}

app = FastAPI(
    title="Multi-Route LLM API",
    version="1.0.0",
    description=(
        "RESTful APIs for AI-powered text analysis that routes each NLP task "
        "(classify, sentiment, summarize, intent) to an Ollama Cloud model "
        "(default: glm-5.2). Each task type is configurable via environment variables."
    ),
    docs_url="/swagger-ui.html",
    openapi_url="/api-docs",
    contact={
        "name": "AI API Support",
        "email": "support@example.com",
    },
    servers=[
        {"url": "/", "description": "Current server"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)


def custom_openapi():
    """Ensure Swagger Try-it-out prefills a valid JSON body (avoids 422 on {})."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=[{"url": "/", "description": "Current server"}],
        contact=app.contact,
    )

    schemas = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
    if "TextRequest" in schemas:
        schemas["TextRequest"]["example"] = _REQUEST_EXAMPLE
        schemas["TextRequest"].pop("examples", None)
        schemas["TextRequest"].pop("required", None)

    for path in (
        "/api/ai/classify",
        "/api/ai/sentiment",
        "/api/ai/summarize",
        "/api/ai/intent",
    ):
        post = openapi_schema.get("paths", {}).get(path, {}).get("post")
        if not post:
            continue
        content = (
            post.setdefault("requestBody", {})
            .setdefault("content", {})
            .setdefault("application/json", {})
        )
        content["example"] = _REQUEST_EXAMPLE
        content.pop("examples", None)

    openapi_schema["servers"] = [{"url": "/", "description": "Current server"}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=True)
