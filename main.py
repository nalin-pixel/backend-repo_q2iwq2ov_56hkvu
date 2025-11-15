import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Menuitem, Order, Orderitem

app = FastAPI(title="Food Ordering API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food Ordering API running"}

@app.get("/schema")
def get_schema():
    # Flames database viewer uses this
    return {"schemas": [
        "user", "product", "menuitem", "order"
    ]}

@app.get("/menu")
def list_menu():
    try:
        items = get_documents("menuitem")
        # Convert ObjectId to string
        for i in items:
            if "_id" in i and isinstance(i["_id"], ObjectId):
                i["id"] = str(i.pop("_id"))
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/menu")
def create_menu_item(item: Menuitem):
    try:
        new_id = create_document("menuitem", item)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateOrderPayload(BaseModel):
    items: List[Orderitem]
    customer_name: str | None = None
    customer_phone: str | None = None
    delivery_address: str | None = None

@app.post("/orders")
def create_order(payload: CreateOrderPayload):
    try:
        total = sum(i.price * i.quantity for i in payload.items)
        order = Order(
            items=payload.items,
            total=total,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            delivery_address=payload.delivery_address,
        )
        new_id = create_document("order", order)
        return {"id": new_id, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
