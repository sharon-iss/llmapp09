from pydantic import BaseModel, ConfigDict, Field

_SAMPLE = "I love this product! The quality is outstanding."


class TextRequest(BaseModel):
    """Request body containing text to analyze."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"text": _SAMPLE},
        }
    )

    # Default prevents Swagger Try-it-out from sending {} → 422
    text: str = Field(
        default=_SAMPLE,
        description="Text to be analyzed",
        examples=[_SAMPLE],
    )
