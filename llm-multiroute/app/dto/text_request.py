from pydantic import BaseModel, ConfigDict, Field

_SAMPLE = "I love this product! The quality is outstanding."


class TextRequest(BaseModel):
    """Request body containing text to analyze."""

    # Singular "example" prefills Swagger Try-it-out.
    # Default value prevents 422 when Swagger sends {} before the user edits.
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"text": _SAMPLE},
        }
    )

    text: str = Field(
        default=_SAMPLE,
        description="Text to be analyzed",
        examples=[_SAMPLE],
    )
