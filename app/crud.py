from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Book).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_reservations(db: Session, user_id: int, skip: int = 0, limit: int = 5):
    return db.query(models.Reservation).filter(models.Reservation.user_id ==
            user_id).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, login: str, password: str):
    user = None
    try:
        user_id = int(login)  # Спробуємо перетворити на число (ID)
        user = db.query(models.User).filter(models.User.id == user_id).first()
    except ValueError:
        # Якщо не число, шукаємо по email
        user = get_user_by_email(db, login)
    
    if not user:
        print(f"User not found: {login}")  # Дебаг
        return False
    if not pwd_context.verify(password, user.password_hash):
        print(f"Password mismatch for: {login}")  # Дебаг
        return False
    return user

def create_user(db: Session, user_data):
    print(f"Creating user: {user_data.name}, {user_data.email}")  # Дебаг
    role = db.query(models.Role).filter(models.Role.name == user_data.role_name).first()
    if not role:
        role = models.Role(name=user_data.role_name)
        db.add(role)
        db.flush()
        print(f"Created role: {user_data.role_name}")  # Дебаг
    hashed_password = pwd_context.hash(user_data.password)
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