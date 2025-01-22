from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jcommerce-web-application.vercel.app"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Database connection details (use environment variables for security)
DB_URL = os.getenv("DB_URL", "postgresql://postgres.dajcekyqugcgteookxfb:DNWhZ7UsPWnMxbN0@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres")

# Database connection initialization
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# Initialize connection
@app.on_event("startup")
async def startup():
    # Establish connection when the application starts
    pass

@app.on_event("shutdown")
def shutdown():
    # Close database connection on shutdown
    pass

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
    conn = get_db_connection()
    cursor = conn.cursor()
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
    finally:
        cursor.close()
        conn.close()

# Get All Products
@app.get("/products/", response_model=List[Product])
def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM products;")
        products = cursor.fetchall()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {e}")
    finally:
        cursor.close()
        conn.close()

# Get a Product by ID
@app.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s;", (product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {e}")
    finally:
        cursor.close()
        conn.close()

# Update a Product
@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, updated_product: Product):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    finally:
        cursor.close()
        conn.close()

# Delete a Product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    finally:
        cursor.close()
        conn.close()

# User model for login request
class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/logins/")
async def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM "public"."user"
            WHERE "email" = %s AND "account_type" = 'admin' AND "status" = 'active';
        """, (user.email,))
        user_record = cursor.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found or inactive admin account")

        # Use column names instead of indexes to avoid errors
        if not bcrypt.checkpw(user.password.encode('utf-8'), user_record["password"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid password")

        return {"message": "Login successful", "user": user_record["email"]}

    except Exception as e:
        print(f"Error during login: {e}")  # Log the exception
        raise HTTPException(status_code=500, detail=f"Error during login: {e}")
    
    finally:
        cursor.close()
        conn.close()