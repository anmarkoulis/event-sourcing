from pydantic import BaseModel, ConfigDict


class ModelConfigBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
