from typing import Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    interests: Optional[List[str]] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    interests: Optional[List[str]] = None

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

class PropertyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=1, max_length=20)
    country: Optional[str] = Field("USA", max_length=100)
    price_per_night: float = Field(..., gt=0)
    amenities: Optional[List[str]] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=1, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    price_per_night: Optional[float] = Field(None, gt=0)
    amenities: Optional[List[str]] = None

class PropertyResponse(PropertyBase):
    id: int

    class Config:
        orm_mode = True

class ReservationBase(BaseModel):
    user_id: int
    property_id: int
    check_in_date: date
    check_out_date: date

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    user_id: Optional[int] = None
    property_id: Optional[int] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None

class ReservationResponse(ReservationBase):
    id: int
    reservation_date: date

    class Config:
        orm_mode = True
