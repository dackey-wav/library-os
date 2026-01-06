from datetime import timedelta, timezone, datetime, date
from dotenv import load_dotenv

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text, select, exists
from . import models

import jwt
from pwdlib import PasswordHash
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

password_hash = PasswordHash.recommended()

def get_books(
        db: Session,
        skip: int = 0, limit: int = 100,
        sort: str | None = None, 
        genre_id: int | None = None,
        author_id: int | None = None,
        search: str | None = None
        ):
    
    query = db.query(models.Book).options(
        joinedload(models.Book.author),
        joinedload(models.Book.genre)
    )

    if genre_id is not None:
        query = query.filter(models.Book.genre_id == genre_id)

    if author_id is not None:
        query = query.filter(models.Book.author_id == author_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Book.title.ilike(search_pattern),
                models.Book.author.has(models.Author.name.ilike(search_pattern))
            )
        )

    if sort is not None:
        if sort == "asc":
            query = query.order_by(models.Book.title.asc())
        elif sort == "desc":
            query = query.order_by(models.Book.title.desc())   

    total_items = query.count()
    books = query.offset(skip).limit(limit).all()

    return books, total_items

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_reservations(db: Session, user_id: int, skip: int = 0, limit: int = 5):
    stmt = select(models.Reservation).where(
        models.Reservation.return_date < date.today(),
        models.Reservation.status == 'active'
    )

    overdue_reservations = db.execute(stmt).scalars().all()

    for res in overdue_reservations:
        res.status = 'overdue'

    db.commit()    

    return db.query(models.Reservation).options(
        joinedload(models.Reservation.book).joinedload(models.Book.author),
        joinedload(models.Reservation.book).joinedload(models.Book.genre)
        ).filter(
            models.Reservation.user_id == user_id,
            models.Reservation.status.in_(['active', 'overdue'])
        ).order_by(models.Reservation.return_date.asc()).offset(skip).limit(limit).all()

def get_genres(db: Session):
    return db.query(models.Genre).all()

def get_authors(db: Session):
    return db.query(models.Author).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, login: str, password: str):
    user = get_user_by_email(db, login)

    if not user:
        print(f"User not found: {login}")
        return False
    if not password_hash.verify(password, user.password_hash):
        print(f"Password mismatch for: {login}")
        return False
    return user

def create_user(db: Session, user_data):
    print(f"Creating user: {user_data.name}, {user_data.email}")
    role = db.query(models.Role).filter(models.Role.name == 'user').first()
    if not role:
        role = models.Role(name='user')
        db.add(role)
        db.flush()
    hashed_password = password_hash.hash(user_data.password)
    db_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role_id=role.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_reservation(db: Session, reservation_data):
    stmt_available = select(
        exists().where(
            models.Book.id == reservation_data.book_id,
            models.Book.count > 0
        )
    ) 
    
    available = db.execute(stmt_available).scalar()
    if not available:
        return False
    
    stmt_same_reservation = select(
        exists().where(
            models.Reservation.book_id == reservation_data.book_id,
            models.Reservation.user_id == reservation_data.user_id
        )
    )

    same = db.execute(stmt_same_reservation).scalar()
    if same:
        return False

    new_reservation = models.Reservation(
        book_id=reservation_data.book_id,
        user_id=reservation_data.user_id,
        return_date=reservation_data.return_date
    )
    db.add(new_reservation)
    book = db.query(models.Book).filter(models.Book.id == reservation_data.book_id).first()
    if book:
        book.count -= 1
    db.commit()
    db.refresh(new_reservation)
    return new_reservation


def return_reservation(db: Session, reservation_id: int):
    reservation = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id,
        models.Reservation.status == "active"
    ).first()
    
    if not reservation:
        return None
    
    reservation.status = "returned"
    
    book = db.query(models.Book).filter(models.Book.id == reservation.book_id).first()
    if book:
        book.count += 1
    
    db.commit()
    db.refresh(reservation)
    return reservation