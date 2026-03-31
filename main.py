from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr 

app = FastAPI(title="Ads Moderation Service")


class PredictRequest(BaseModel):
    seller_id: StrictInt = Field(..., gt=0)
    is_verified_seller: StrictBool
    item_id: StrictInt = Field(..., gt=0)
    name: StrictStr = Field(..., min_length=1)
    description: StrictStr = Field(..., min_length=1)
    category: StrictInt = Field(..., gt=0)
    images_qty: StrictInt = Field(..., ge=0)


def predict_violation(payload: PredictRequest) -> bool:
    if payload.is_verified_seller:
        return False

    return payload.images_qty == 0


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/predict", response_model=bool)
async def predict(payload: PredictRequest) -> bool:
    try:
        return predict_violation(payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal prediction error")
