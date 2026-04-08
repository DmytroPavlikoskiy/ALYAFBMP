from pydantic import BaseModel


class OrderCreateBody(BaseModel):
    product_id: int


class OrderCreatedResponse(BaseModel):
    order_id: int
