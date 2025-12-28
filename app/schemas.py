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

class UserLogin(BaseModel):
    login: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str = Field(..., min_length=8, max_length=64)

class ReservationCreate(BaseModel):
    user_id: int
    book_id: int
    return_date: date

    class Config:
        from_attributes = True