from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base schema that rejects unknown fields for reliable JSON contracts."""

    model_config = ConfigDict(extra="forbid")
