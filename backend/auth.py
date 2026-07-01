import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
import bcrypt

from database import get_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing setup
# Using bcrypt directly since passlib has known issues with bcrypt >= 4.0.0

# Temporary in-memory OTP store. 
# Format: { "email@example.com": {"otp": "123456", "expires_at": datetime} }
otp_store: Dict[str, dict] = {}

# Credentials for email
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- Schemas ---

class RequestOTPRequest(BaseModel):
    name: str
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Helper Functions ---

def send_otp_email(to_email: str, name: str, otp: str):
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"Warning: Email credentials not configured. OTP for {to_email} is {otp}")
        return

    subject = "Your Heart Disease Predictor OTP"
    body = f"Hello {name},\n\nYour OTP for registration is: {otp}\n\nIt is valid for 10 minutes."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    try:
        # Assuming Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
            print(f"OTP email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        # Not throwing exception here so development can continue even if email fails, 
        # though in production you'd want to handle this.

# --- Endpoints ---

@router.post("/request-otp")
def request_otp(req: RequestOTPRequest, background_tasks: BackgroundTasks):
    # Check if user already exists
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists with this email.")

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store OTP with 10 minute expiry
    expires_at = datetime.now() + timedelta(minutes=10)
    otp_store[req.email] = {"otp": otp, "expires_at": expires_at}

    # Send email in background
    background_tasks.add_task(send_otp_email, req.email, req.name, otp)

    return {"message": "OTP sent successfully. Please check your email."}

@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    record = otp_store.get(req.email)
    
    if not record:
        raise HTTPException(status_code=400, detail="No OTP requested for this email.")
    
    if datetime.now() > record["expires_at"]:
        del otp_store[req.email]
        raise HTTPException(status_code=400, detail="OTP has expired.")
        
    if record["otp"] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    # OTP is verified. We can mark it as verified or just let the client proceed to signup.
    # For simplicity, we'll mark it verified in the store.
    otp_store[req.email]["verified"] = True

    return {"message": "OTP verified successfully."}

@router.post("/signup")
def signup(req: SignupRequest):
    # Verify they have a verified OTP
    record = otp_store.get(req.email)
    if not record or not record.get("verified"):
        raise HTTPException(status_code=400, detail="Please verify OTP first.")

    # Check again if user exists just to be safe
    if get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="User already exists.")

    # Hash password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), salt).decode('utf-8')

    # Save to Fluxbase
    create_user(req.name, req.email, hashed_password)

    # Clean up OTP store
    del otp_store[req.email]

    return {"message": "User registered successfully."}

@router.post("/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not bcrypt.checkpw(req.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Return a basic user info payload (in a real app, return a JWT)
    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        },
        "token": f"fake-token-{user['id']}" # Mock token for frontend checks
    }
