# /generate-description

from fastapi import APIRouter
from pydantic import BaseModel
from services.description_gen import generate_description

router = APIRouter(prefix="/generate-description", tags=["Product Description"])

class Product(BaseModel):
    title: str
    category: str
    brand: str

@router.post("/")
def gen_desc(product: Product):
    desc = generate_description(product.title, product.category, product.brand)
    return {"description": desc}
