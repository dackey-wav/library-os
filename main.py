from typing import Annotated
from datetime import timedelta

import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from datetime import timedelta, timezone, datetime

from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.db import SessionLocal, engine

import os
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/dataset", StaticFiles(directory=r"data\dataset"), name="dataset")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db)
        ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id_from_token = payload.get("sub")
        if user_id_from_token is None:
            raise credentials_exception
        
        user_id_from_token = int(user_id_from_token)
        token_data = schemas.TokenData(user_id=user_id_from_token)
    except InvalidTokenError as e:
        raise credentials_exception
    
    user = crud.get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


@app.get("/api/users/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/api/books/", response_model=schemas.BookPage)
def read_books(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 8,
    genre_id: int | None = None,
    author_id: int | None = None,
    search: str | None = None,
    sort: str | None = None
    ):

    books, total_items = crud.get_books(
        db, skip=skip, limit=limit, genre_id=genre_id,
        author_id=author_id, search=search, sort=sort)
    
    if genre_id or author_id or search:
        analytics = models.SearchEvents(
            user_id=current_user.id,
            genre_id=genre_id,
            author_id=author_id,
            query_text=search,
            created_at=datetime.now(timezone.utc)
        )
        db.add(analytics)
        db.commit()

    return {"items": books, "total_items": total_items, "skip": skip, "limit": limit}


@app.get("/api/users/{user_id}/reservations/", response_model=list[schemas.Reservation])
def read_user_reservations(
    user_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    reservations = crud.get_user_reservations(db, user_id=user_id)
    return reservations


@app.get("/api/genres/", response_model=list[schemas.Genre])
def read_genres(db: Session = Depends(get_db)):
    genres = crud.get_genres(db)
    return genres


@app.get("/api/authors/", response_model=list[schemas.Author])
def read_authors(db: Session = Depends(get_db)):
    authors = crud.get_authors(db)
    return authors


@app.get("/api/me", response_model=schemas.User)
def read_users_me(current_user: Annotated[schemas.User, Depends(get_current_user)]):
    return current_user


@app.post("/token", response_model=schemas.Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
    ) -> schemas.Token:
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.post("/api/register", response_model=schemas.User)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_data)
    return user


@app.get("/")
def index():
    return FileResponse(path="static/index.html")


# @app.get("/login")
# def login_page():
#     return FileResponse(path="static/login.html")


@app.post("/api/reservations/", response_model=schemas.Reservation)
def create_loan(
    reservation: schemas.ReservationCreate,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if current_user.id != reservation.user_id:
        raise HTTPException(status_code=403, detail="Cannot reserve for another user")
    
    new_reservation = crud.create_reservation(db, reservation_data=reservation)
    if not new_reservation:
        raise HTTPException(status_code=400, detail="Cannot create reservation")
    return new_reservation


@app.patch("/api/reservations/{reservation_id}/return", response_model=schemas.Reservation)
def return_loan(
    reservation_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot return another user's reservation")

    result = crud.return_reservation(db, reservation_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot return this reservation")
    return result


@app.get("/api/users/{user_id}/history/", response_model=list[schemas.Reservation])
def read_user_history(
    user_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = crud.get_user_history(db, user_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot return this user history")
    return result

@app.get("/api/users/{user_id}/analytics/", response_model=schemas.Statistics)
def read_user_stats(
    user_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = crud.get_user_stats(db, user_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot return this user history")
    return result