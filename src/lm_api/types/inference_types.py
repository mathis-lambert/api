from pydantic import BaseModel


class Model(BaseModel):
    name: str
    version: str
