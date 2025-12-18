from pydantic import BaseModel
from datetime import date


class Book(BaseModel):
    id: int
    title: str
    isbn: str
    count: int
    cover_path: str | None = None
    author_name: str | None = None
    genre_name: str | None = None

    class Config:
        from_attributes = True


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


class Reservation(BaseModel):
    id: int
    reserve_date: date
    return_date: date | None = None
    status: str
    book: Book

    class Config:
        from_attributes = True
        
class UserLogin(BaseModel):
    login: str  # Тепер "login" замість "email" — може бути ID (число) або email
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role_name: str = "user"  # За замовчуванням "user", можна змінити на "student" або "teacher"
