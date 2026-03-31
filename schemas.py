from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr


class PredictRequest(BaseModel):
    seller_id: StrictInt = Field(..., gt=0)
    is_verified_seller: StrictBool
    item_id: StrictInt = Field(..., gt=0)
    name: StrictStr = Field(..., min_length=1)
    description: StrictStr = Field(..., min_length=1)
    category: StrictInt = Field(..., gt=0)
    images_qty: StrictInt = Field(..., ge=0)


class PredictResponse(BaseModel):
    is_violation: bool
    probability: float = Field(..., ge=0.0, le=1.0)
