from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base com config ORM-friendly."""

    model_config = ConfigDict(from_attributes=True)
