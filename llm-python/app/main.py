from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.controller.ai_controller import router as ai_router

_REQUEST_EXAMPLE = {
    "text": "I love this product! The quality is outstanding.",
}

app = FastAPI(
    title="Spring AI with Ollama - Text Analysis API",
    version="1.0.0",
    description=(
        "RESTful APIs for AI-powered text analysis including classification, "
        "sentiment analysis, summarization, and intent detection using "
        "Ollama Cloud (default model: glm-5.2)."
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
