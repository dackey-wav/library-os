from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.db import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/api/books/", response_model=list[schemas.Book])
def read_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = crud.get_books(db, skip=skip, limit=limit)
    return books
    
@app.get("/api/users/{user_id}/reservations/", response_model=list[schemas.Reservation])
def read_user_reservations(user_id: int, db: Session = Depends(get_db)):
    reservations = crud.get_user_reservations(db, user_id=user_id)
    for res in reservations:
        if res.book:
            if res.book.author:
                res.book.author_name = res.book.author.name
            else:
                res.book.author_name = "Unknown"

            if res.book.genre:
                res.book.genre_name = res.book.genre.name
            else:
                res.book.genre_name = "Unknown"
    return reservations

@app.post("/api/login", response_model=schemas.User)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    print(f"Login attempt: {user_credentials.login}")  # Дебаг
    user = crud.authenticate_user(db, user_credentials.login, user_credentials.password)
    if not user:
        print("Authentication failed")  # Дебаг
        raise HTTPException(status_code=400, detail="Incorrect login or password")
    print(f"Login successful: {user.name}")  # Дебаг
    return user

@app.post("/api/register", response_model=schemas.User)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_data)
    return user

