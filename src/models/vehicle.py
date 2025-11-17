from pydantic import BaseModel, Field


class VehicleRequest(BaseModel):
    length: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Vehicle(BaseModel):
    length: int
    width: int = 10

