from __future__ import annotations
from typing import Annotated
from datetime import date
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, Enum as SQLEnum, func, MetaData, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum

convention = {
  "ix": "ix_%(column_0_label)s",                                        # indexes
  "uq": "uq_%(table_name)s_%(column_0_name)s",                          # UNIQUE
  "ck": "ck_%(table_name)s_%(constraint_name)s",                        # CHECK
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # FOREIGN KEY
  "pk": "pk_%(table_name)s"                                             # PRIMARY KEY
}

metadata = MetaData(naming_convention=convention)

intpk = Annotated[int, mapped_column(Integer, primary_key=True)]

class Base(DeclarativeBase):
    """Base for all models"""
    metadata = MetaData(naming_convention=convention)


class ReservationStatus(enum.Enum):
    """Reservation Status"""
    active = "active"
    returned = "returned"
    overdue = "overdue"


class Role(Base):
    """User roles: admin, user etc."""
    __tablename__ = "roles"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    """System users"""
    __tablename__ = "users"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))

    role: Mapped[Role] = relationship(back_populates="users")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")
    search_events: Mapped[list["SearchEvents"]] = relationship(back_populates="user")


class Genre(Base):
    """Book genres"""
    __tablename__ = "genres"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    books: Mapped[list["Book"]] = relationship(back_populates="genre")
    search_events: Mapped[list["SearchEvents"]] = relationship(back_populates="genre")


class Author(Base):
    """Authors"""
    __tablename__ = "authors"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(255), nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="author")
    search_events: Mapped[list["SearchEvents"]] = relationship(back_populates="author")


class Book(Base):
    """Books"""
    __tablename__ = "books"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    cover_path: Mapped[str | None] = mapped_column(String(300), nullable=True)

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"))
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="SET NULL"), nullable=True)
    
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    author: Mapped[Author] = relationship(back_populates="books")
    genre: Mapped[Genre | None] = relationship(back_populates="books")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="book")


class Reservation(Base):
    """Book reservations"""
    __tablename__ = "reservations"

    id: Mapped[intpk]
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reserve_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=text("TIMEZONE('utc', now())"))
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ReservationStatus] = mapped_column(
        SQLEnum(ReservationStatus, native_enum=False),
        nullable=False,
        default=ReservationStatus.active,
        server_default="active"
    )

    book: Mapped[Book] = relationship(back_populates="reservations")
    user: Mapped[User] = relationship(back_populates="reservations")

class SearchEvents(Base):
    "History logging for stats"
    __tablename__ = "search_events"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="SET NULL"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), nullable=True)
    query_text: Mapped[str | None] = mapped_column(String(511), nullable=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, server_default=text("TIMEZONE('utc', now())"))

    user: Mapped[User] = relationship(back_populates="search_events")
    genre: Mapped[Genre | None] = relationship(back_populates="search_events")
    author: Mapped[Author | None] = relationship(back_populates="search_events")