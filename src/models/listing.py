from pydantic import BaseModel, Field, field_validator
from typing import List


class Listing(BaseModel):
    id: str
    length: int = Field(gt=0)
    width: int = Field(gt=0)
    location_id: str
    price_in_cents: int = Field(ge=0)
    
    @field_validator('length', 'width')
    @classmethod
    def validate_multiple_of_10(cls, v):
        if v % 10 != 0:
            raise ValueError('length and width must be multiples of 10')
        return v


class LocationResult(BaseModel):
    location_id: str
    listing_ids: List[str]
    total_price_in_cents: int

