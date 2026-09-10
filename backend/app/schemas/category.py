from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    name: str
    is_system: bool

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
