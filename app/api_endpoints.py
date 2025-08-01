import json
import os
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from typing import List
from datetime import date
import models_sqlalchemy as models
import models_pydantic as schemas
from utils import clean_llm_output, get_completion, setup_llm_client
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = models.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Utility Functions ----------
def list_to_comma_string(lst):
    if lst is None:
        return None
    return ",".join([v.strip() for v in lst if v.strip()])

def comma_string_to_list(s):
    if s is None or s.strip() == "":
        return []
    return [v.strip() for v in s.split(",") if v.strip()]

# ---------- User Endpoints ----------
@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(
        name=user.name,
        email=user.email,
        interests=list_to_comma_string(user.interests)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    resp = schemas.UserResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        interests=comma_string_to_list(db_user.interests)
    )
    return resp

@app.get("/users/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [
        schemas.UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            interests=comma_string_to_list(u.interests)
        )
        for u in users
    ]

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        interests=comma_string_to_list(user.interests)
    )

@app.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.email:
        existing = db.query(models.User).filter(models.User.email == user_update.email, models.User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered by another user")
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.interests is not None:
        user.interests = list_to_comma_string(user_update.interests)
    db.commit()
    db.refresh(user)
    return schemas.UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        interests=comma_string_to_list(user.interests)
    )

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return

# ---------- Given a User, invoke an LLM to suggest vacation properties ----------
@app.get("/users/{user_id}/properties", response_model=List[schemas.PropertyResponse])
def get_user_properties(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    props = db.query(models.Property).all()
    
    user_interests = user.interests
    city_state_list = [
    {
        "id": prop.id,
        "name": prop.name,
        "city": prop.city,
        "state": prop.state,
        "amenities": prop.amenities
    }
    for prop in props
    ]

    print("The user has interests: {}".format(user.interests))
    print("There are {} properties in the database".format(len(city_state_list)))

    user_recommendations_prompt = f"""
    You are a travel agent.
    You will be given a set of user interests as well as a detailed list of vacation property locations.
    The property locations include the id, name, city, state, and amenities.
    Recommend a list of properties that align with the user's interests.
    Base your recommendation on the city of the property and what activities are popular there.
    Try to spread your recommendations across different interests and locations, and consider all properties in the list.
    Also, favor unusual destinations that are not too touristy.

    The user's interests are: {user_interests}
    The list of property locations is: {city_state_list}

    Your response should be the list of property ids in JSON format (a JSON array of integers).
    Do not include anything else in your response, and do not repeat property ids.
    Return no more than 5 property ids.
    """
    project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
    client, model_name, api_provider = setup_llm_client(model_name="gpt-4.1-mini")
    property_ids = get_completion(user_recommendations_prompt, client, model_name, api_provider, temperature=0.5)
    print("The LLM returned the following: {}".format(property_ids))
    property_ids = clean_llm_output(property_ids, "json")
    property_ids = json.loads(property_ids)
    property_ids = sorted(set(property_ids))

    print("The LLM recommended the following property ids: {}".format(property_ids))

    responses = []
    for pid in property_ids:
        prop = db.query(models.Property).filter(models.Property.id == pid).first()
        if prop:
            resp = schemas.PropertyResponse(
                id=prop.id,
                name=prop.name,
                address_line1=prop.address_line1,
                address_line2=prop.address_line2,
                city=prop.city,
                state=prop.state,
                zip_code=prop.zip_code,
                country=prop.country,
                price_per_night=prop.price_per_night,
                amenities=comma_string_to_list(prop.amenities)
            )
            responses.append(resp)
    return responses


# ---------- Property Endpoints ----------
@app.post("/properties/", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(property: schemas.PropertyCreate, db: Session = Depends(get_db)):
    db_property = models.Property(
        name=property.name,
        address_line1=property.address_line1,
        address_line2=property.address_line2,
        city=property.city,
        state=property.state,
        zip_code=property.zip_code,
        country=property.country,
        price_per_night=property.price_per_night,
        amenities=list_to_comma_string(property.amenities)
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return schemas.PropertyResponse(
        id=db_property.id,
        name=db_property.name,
        address_line1=db_property.address_line1,
        address_line2=db_property.address_line2,
        city=db_property.city,
        state=db_property.state,
        zip_code=db_property.zip_code,
        country=db_property.country,
        price_per_night=db_property.price_per_night,
        amenities=comma_string_to_list(db_property.amenities)
    )

@app.get("/properties/", response_model=List[schemas.PropertyResponse])
def list_properties(db: Session = Depends(get_db)):
    props = db.query(models.Property).all()
    return [
        schemas.PropertyResponse(
            id=p.id,
            name=p.name,
            address_line1=p.address_line1,
            address_line2=p.address_line2,
            city=p.city,
            state=p.state,
            zip_code=p.zip_code,
            country=p.country,
            price_per_night=p.price_per_night,
            amenities=comma_string_to_list(p.amenities)
        )
        for p in props
    ]

@app.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return schemas.PropertyResponse(
        id=prop.id,
        name=prop.name,
        address_line1=prop.address_line1,
        address_line2=prop.address_line2,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        country=prop.country,
        price_per_night=prop.price_per_night,
        amenities=comma_string_to_list(prop.amenities)
    )

@app.put("/properties/{property_id}", response_model=schemas.PropertyResponse)
def update_property(property_id: int, property_update: schemas.PropertyUpdate, db: Session = Depends(get_db)):
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    for field, value in property_update.dict(exclude_unset=True).items():
        if field == "amenities" and value is not None:
            setattr(prop, field, list_to_comma_string(value))
        elif value is not None:
            setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return schemas.PropertyResponse(
        id=prop.id,
        name=prop.name,
        address_line1=prop.address_line1,
        address_line2=prop.address_line2,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        country=prop.country,
        price_per_night=prop.price_per_night,
        amenities=comma_string_to_list(prop.amenities)
    )

@app.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(prop)
    db.commit()
    return

# ---------- Reservation Endpoints ----------
@app.post("/reservations/", response_model=schemas.ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == reservation.user_id).first()
    prop = db.query(models.Property).filter(models.Property.id == reservation.property_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")
    if not prop:
        raise HTTPException(status_code=400, detail="Property does not exist")
    if reservation.check_in_date >= reservation.check_out_date:
        raise HTTPException(status_code=400, detail="check_out_date must be after check_in_date")
    today = date.today()
    db_reservation = models.Reservation(
        user_id=reservation.user_id,
        property_id=reservation.property_id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        reservation_date=today
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return schemas.ReservationResponse(
        id=db_reservation.id,
        user_id=db_reservation.user_id,
        property_id=db_reservation.property_id,
        check_in_date=db_reservation.check_in_date,
        check_out_date=db_reservation.check_out_date,
        reservation_date=db_reservation.reservation_date
    )

@app.get("/reservations/", response_model=List[schemas.ReservationResponse])
def list_reservations(db: Session = Depends(get_db)):
    reservations = db.query(models.Reservation).all()
    return [
        schemas.ReservationResponse(
            id=r.id,
            user_id=r.user_id,
            property_id=r.property_id,
            check_in_date=r.check_in_date,
            check_out_date=r.check_out_date,
            reservation_date=r.reservation_date
        )
        for r in reservations
    ]

@app.get("/reservations/{reservation_id}", response_model=schemas.ReservationResponse)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return schemas.ReservationResponse(
        id=r.id,
        user_id=r.user_id,
        property_id=r.property_id,
        check_in_date=r.check_in_date,
        check_out_date=r.check_out_date,
        reservation_date=r.reservation_date
    )

@app.put("/reservations/{reservation_id}", response_model=schemas.ReservationResponse)
def update_reservation(reservation_id: int, reservation_update: schemas.ReservationUpdate, db: Session = Depends(get_db)):
    r = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")
    data = reservation_update.dict(exclude_unset=True)
    if "user_id" in data:
        user = db.query(models.User).filter(models.User.id == data["user_id"]).first()
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")
        r.user_id = data["user_id"]
    if "property_id" in data:
        prop = db.query(models.Property).filter(models.Property.id == data["property_id"]).first()
        if not prop:
            raise HTTPException(status_code=400, detail="Property does not exist")
        r.property_id = data["property_id"]
    if "check_in_date" in data:
        r.check_in_date = data["check_in_date"]
    if "check_out_date" in data:
        r.check_out_date = data["check_out_date"]
    if r.check_in_date >= r.check_out_date:
        raise HTTPException(status_code=400, detail="check_out_date must be after check_in_date")
    db.commit()
    db.refresh(r)
    return schemas.ReservationResponse(
        id=r.id,
        user_id=r.user_id,
        property_id=r.property_id,
        check_in_date=r.check_in_date,
        check_out_date=r.check_out_date,
        reservation_date=r.reservation_date
    )

@app.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db.delete(r)
    db.commit()
    return
