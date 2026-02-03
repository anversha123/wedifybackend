from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
import os

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas ---
# Used for Request/Response validation

class BookingRequestBase(BaseModel):
    venueId: int
    userEmail: str
    date: str
    guestCount: int
    requirements: Optional[dict] = None
    status: str = "pending"

class BookingRequestCreate(BookingRequestBase):
    pass

class BookingRequest(BookingRequestBase):
    id: int # Changed to int to match DB
    
    class Config:
        orm_mode = True

class RequestStatusUpdate(BaseModel):
    status: str

class PlannerBase(BaseModel):
    name: str
    contact: str
    location: str
    basePrice: int
    description: str
    image: str

class PlannerCreate(PlannerBase):
    pass

class Planner(PlannerBase):
    id: int
    
    class Config:
        orm_mode = True

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Wedify Backend Running with SQLite"}

# --- Booking Endpoints ---

@app.get("/api/bookings", response_model=List[BookingRequest])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(models.BookingRequest).all()
    return bookings

@app.post("/api/bookings", response_model=BookingRequest)
def create_booking(request: BookingRequestCreate, db: Session = Depends(get_db)):
    # Create DB model instance
    db_booking = models.BookingRequest(
        venueId=request.venueId,
        userEmail=request.userEmail,
        date=request.date,
        guestCount=request.guestCount,
        requirements=request.requirements,
        status=request.status
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@app.delete("/api/bookings/{request_id}")
def delete_booking(request_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.BookingRequest).filter(models.BookingRequest.id == request_id).first()
    if not booking:
         raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted"}

@app.put("/api/bookings/{request_id}/status", response_model=BookingRequest)
def update_booking_status(request_id: int, status_update: RequestStatusUpdate, db: Session = Depends(get_db)):
    booking = db.query(models.BookingRequest).filter(models.BookingRequest.id == request_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if status_update.status not in ["approved", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    booking.status = status_update.status
    db.commit()
    db.refresh(booking)
    return booking

# --- Planner Endpoints ---

@app.get("/api/planners", response_model=List[Planner])
def get_planners(db: Session = Depends(get_db)):
    planners = db.query(models.Planner).all()
    # Seed initial data if empty (optional, for demo purposes)
    if not planners:
        initial_planner = models.Planner(
            name="Elite Wedding Planners",
            contact="+91 98765 43210",
            location="Mumbai",
            basePrice=50000,
            description="Premium wedding planning services with over 10 years of experience.",
            image="https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&q=80&w=800"
        )
        db.add(initial_planner)
        db.commit()
        db.refresh(initial_planner)
        planners = [initial_planner]
    return planners

@app.post("/api/planners", response_model=Planner)
def create_planner(planner: PlannerCreate, db: Session = Depends(get_db)):
    db_planner = models.Planner(
        name=planner.name,
        contact=planner.contact,
        location=planner.location,
        basePrice=planner.basePrice,
        description=planner.description,
        image=planner.image
    )
    db.add(db_planner)
    db.commit()
    db.refresh(db_planner)
    return db_planner


# --- Payment Endpoints ---
import stripe

# REPLACE WITH YOUR STRIPE SECRET KEY
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")


class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "inr"

@app.post("/api/create-payment-intent")
def create_payment_intent(request: PaymentIntentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return {"clientSecret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
