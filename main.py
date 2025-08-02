from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import jwt
from supabase import create_client, Client
import uvicorn
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime

app = FastAPI(title="Book Tracker API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET]):
    raise ValueError("Missing required environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Security
security = HTTPBearer()


# Pydantic models
class BookCreate(BaseModel):
    title: str
    author: str
    status: str = "reading"


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    status: str
    created_at: str
    user_id: str


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Routes
@app.get("/")
async def root():
    return {"message": "Book Tracker API is running!"}


@app.post("/books", response_model=BookResponse)
async def create_book(book: BookCreate, user_id: str = Depends(get_current_user)):
    # Validate status
    valid_statuses = ["reading", "completed", "wishlist"]
    if book.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(valid_statuses)}"
        )

    try:
        # Insert book into database
        result = supabase.table("books").insert({
            "title": book.title,
            "author": book.author,
            "status": book.status,
            "user_id": user_id
        }).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create book"
            )

        return result.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/books", response_model=List[BookResponse])
async def get_books(
        status_filter: Optional[str] = None,
        user_id: str = Depends(get_current_user)
):
    try:
        query = supabase.table("books").select("*").eq("user_id", user_id)

        # Apply status filter if provided
        if status_filter:
            valid_statuses = ["reading", "completed", "wishlist"]
            if status_filter not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status filter must be one of: {', '.join(valid_statuses)}"
                )
            query = query.eq("status", status_filter)

        result = query.order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/books/{book_id}")
async def delete_book(book_id: str, user_id: str = Depends(get_current_user)):
    try:
        # Check if book exists and belongs to user
        existing_book = supabase.table("books").select("*").eq("id", book_id).eq("user_id", user_id).execute()

        if not existing_book.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Delete the book
        result = supabase.table("books").delete().eq("id", book_id).eq("user_id", user_id).execute()

        return {"message": "Book deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.patch("/books/{book_id}", response_model=BookResponse)
async def update_book(
        book_id: str,
        book_update: BookUpdate,
        user_id: str = Depends(get_current_user)
):
    try:
        # Check if book exists and belongs to user
        existing_book = supabase.table("books").select("*").eq("id", book_id).eq("user_id", user_id).execute()

        if not existing_book.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Prepare update data
        update_data = {}
        if book_update.title is not None:
            update_data["title"] = book_update.title
        if book_update.author is not None:
            update_data["author"] = book_update.author
        if book_update.status is not None:
            valid_statuses = ["reading", "completed", "wishlist"]
            if book_update.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of: {', '.join(valid_statuses)}"
                )
            update_data["status"] = book_update.status

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update the book
        result = supabase.table("books").update(update_data).eq("id", book_id).eq("user_id", user_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update book"
            )

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)