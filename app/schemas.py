from pydantic import BaseModel, Field
from datetime import date

class Role(BaseModel):
    name: str

    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    name: str
    email: str
    role: Role

    class Config:
        from_attributes = True


class Genre(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class Author(BaseModel):
   id: int
   name: str

   class Config:
    from_attributes = True

class Book(BaseModel):
    id: int
    title: str
    isbn: str
    count: int
    cover_path: str | None = None
    author: Author | None = None
    genre: Genre | None = None

    class Config:
        from_attributes = True

class BookPage(BaseModel):
    items: list[Book]
    total_items: int
    skip: int
    limit: int

    class Config:
        from_attributes = True

class Reservation(BaseModel):
    id: int
    reserve_date: date
    return_date: date | None = None
    status: str
    book: Book

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    name: str
    email: str
    password: str = Field(..., min_length=8, max_length=64)

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    user_id: int

    class Config:
        from_attributes = True

class ReservationCreate(BaseModel):
    user_id: int
    book_id: int
    return_date: date

    class Config:
        from_attributes = True

class Statistics(BaseModel):
    top_author: str
    top_genre: str
    total_queries: int
    total_read: int
    on_hand: int
    fav_genre: str

    class Config:
            from_attributes = True