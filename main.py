from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from typing import List

app = FastAPI(prefix="/api/v1/orders", tags=["Orders"])



@app.post("/", response_model=schemas.OrderRead, status_code=201)
async def create_order(
        payload: schemas.OrderCreate,
        db: Session = Depends(get_db),
        current_user_id: str = "current-uuid-from-jwt"
):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_order = models.Order(
        buyer_id=current_user_id,
        product_id=payload.product_id,
        status="CREATED"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/history", response_model=List[schemas.OrderRead])
async def get_my_orders(
        db: Session = Depends(get_db),
        current_user_id: str = "current-uuid-from-jwt"
):
    orders = db.query(models.Order).filter(models.Order.buyer_id == current_user_id).all()
    return orders
