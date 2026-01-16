from datetime import timedelta, timezone, datetime, date
from dotenv import load_dotenv

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text, select, exists, case, func, desc
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
        models.Reservation.status != "returned"
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

def get_user_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    status_order = case(
    (models.Reservation.status == "overdue", 1),
    (models.Reservation.status == "active", 2),
    (models.Reservation.status == "returned", 3),
    else_=4  
    )

    return db.query(models.Reservation).options(
        joinedload(models.Reservation.book).joinedload(models.Book.author),
        joinedload(models.Reservation.book).joinedload(models.Book.genre)
    ).filter(
        models.Reservation.user_id == user_id
    ).order_by(status_order, models.Reservation.reserve_date.desc()).offset(skip).limit(limit).all()

def get_user_stats(db, user_id: int, period_days: int = 30):
    cutoff = date.today() - timedelta(days=period_days)

    stmt_top_genre = (
        select(models.Genre.name)
        .select_from(models.SearchEvents)
        .join(models.Genre, models.SearchEvents.genre_id == models.Genre.id)
        .where(
            models.SearchEvents.user_id == user_id,
            models.SearchEvents.created_at >= cutoff,
            models.SearchEvents.genre_id.isnot(None),
        )
        .group_by(models.Genre.name)
        .order_by(func.count().desc())
        .limit(1)
    )
    top_genre = db.execute(stmt_top_genre).scalar()

    stmt_top_author = (
        select(models.Author.name)
        .select_from(models.SearchEvents)
        .join(models.Author, models.SearchEvents.author_id == models.Author.id)
        .where(
            models.SearchEvents.user_id == user_id,
            models.SearchEvents.created_at >= cutoff,
            models.SearchEvents.author_id.isnot(None),
        )
        .group_by(models.Author.name)
        .order_by(func.count().desc())
        .limit(1)
    )
    top_author = db.execute(stmt_top_author).scalar()

    total_queries = db.execute(
        select(func.count()).select_from(models.SearchEvents).where(models.SearchEvents.user_id == user_id)
    ).scalar() or 0

    total_read = db.execute(
        select(func.count())
        .select_from(models.Reservation)
        .where(
            models.Reservation.user_id == user_id,
            models.Reservation.status == models.ReservationStatus.returned,
        )
    ).scalar() or 0

    on_hand = db.execute(
        select(func.count())
        .select_from(models.Reservation)
        .where(
            models.Reservation.user_id == user_id,
            models.Reservation.status.in_(['active', 'overdue']),
        )
    ).scalar() or 0

    stmt_fav_genre = (
        select(models.Genre.name)
        .select_from(models.Reservation)
        .join(models.Book, models.Reservation.book_id == models.Book.id)
        .join(models.Genre, models.Book.genre_id == models.Genre.id)
        .where(
            models.Reservation.user_id == user_id,
            models.Reservation.status == models.ReservationStatus.returned,
        )
        .group_by(models.Genre.name)
        .order_by(func.count().desc())
        .limit(1)
    )
    fav_genre = db.execute(stmt_fav_genre).scalar()

    return {
        "top_author": top_author or "N/A",
        "top_genre": top_genre or "N/A",
        "total_queries": int(total_queries),
        "total_read": int(total_read),
        "on_hand": int(on_hand),
        "fav_genre": fav_genre or "N/A",
    }