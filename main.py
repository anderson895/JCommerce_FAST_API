from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI()

# Database connection details (use environment variables for security)
DB_URL = "postgresql://postgres.dajcekyqugcgteookxfb:DNWhZ7UsPWnMxbN0@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

# Database connection initialization
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# Initialize connection
conn = get_db_connection()
cursor = conn.cursor()

# Product model
class Product(BaseModel):
    product_id: Optional[int] = None  # Auto-incremented by the database
    product_picture: Optional[str] = None
    product_name: str
    product_price: float
    product_description: Optional[str] = None
    product_stocks: int

# Create a Product
@app.post("/products/", response_model=Product)
def create_product(product: Product):
    try:
        query = """
            INSERT INTO products (product_picture, product_name, product_price, product_description, product_stocks)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
        """
        cursor.execute(query, (
            product.product_picture,
            product.product_name,
            product.product_price,
            product.product_description,
            product.product_stocks
        ))
        conn.commit()
        new_product = cursor.fetchone()
        return new_product
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {e}")

# Get All Products
@app.get("/products/", response_model=List[Product])
def get_all_products():
    try:
        cursor.execute("SELECT * FROM products;")
        products = cursor.fetchall()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {e}")

# Get a Product by ID
@app.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: int):
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s;", (product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {e}")

# Update a Product
@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, updated_product: Product):
    try:
        query = """
            UPDATE products
            SET product_picture = %s,
                product_name = %s,
                product_price = %s,
                product_description = %s,
                product_stocks = %s
            WHERE product_id = %s
            RETURNING *;
        """
        cursor.execute(query, (
            updated_product.product_picture,
            updated_product.product_name,
            updated_product.product_price,
            updated_product.product_description,
            updated_product.product_stocks,
            product_id
        ))
        conn.commit()
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating product: {e}")

# Delete a Product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    try:
        cursor.execute("DELETE FROM products WHERE product_id = %s RETURNING *;", (product_id,))
        conn.commit()
        deleted_product = cursor.fetchone()
        if not deleted_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"detail": "Product deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product: {e}")

# Close database connection on shutdown
@app.on_event("shutdown")
def shutdown():
    if conn:
        cursor.close()
        conn.close()
