from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Text, create_engine, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

DATABASE_URL = "sqlite:///./travel.db"

Base = declarative_base()

class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    interests = Column(Text, nullable=True)  # comma-separated

    reservations = relationship("Reservation", back_populates="user", cascade="all, delete-orphan")

class Property(Base):
    __tablename__ = "Properties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False, default="USA")
    price_per_night = Column(Float, nullable=False)
    amenities = Column(Text, nullable=True)  # comma-separated

    reservations = relationship("Reservation", back_populates="property", cascade="all, delete-orphan")

class Reservation(Base):
    __tablename__ = "Reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("Properties.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    reservation_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="reservations")
    property = relationship("Property", back_populates="reservations")

Index("ix_users_email", User.email, unique=True)
UniqueConstraint("email", name="uq_users_email")
