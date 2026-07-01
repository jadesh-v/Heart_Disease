import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
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

APP_NAME = "Heart Disease Predictor"

def send_otp_email(to_email: str, name: str, otp: str):
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"Warning: Email credentials not configured. OTP for {to_email} is {otp}")
        return

    subject = f"Your {APP_NAME} OTP Code"

    plain_body = (
        f"Hello {name},\n\n"
        f"Your One-Time Password (OTP) for {APP_NAME} is:\n\n"
        f"  {otp}\n\n"
        f"This code is valid for 10 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— The {APP_NAME} Team"
    )

    html_body = f"""\
<html>
  <body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:32px;">
    <div style="max-width:480px;margin:auto;background:#fff;border-radius:12px;padding:36px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
      <h2 style="color:#1e3a5f;margin-bottom:8px;">&#128147; {APP_NAME}</h2>
      <p style="color:#555;font-size:15px;">Hello <strong>{name}</strong>,</p>
      <p style="color:#555;font-size:15px;">Use the OTP below to complete your registration:</p>
      <div style="text-align:center;margin:28px 0;">
        <span style="display:inline-block;background:#1e3a5f;color:#fff;font-size:32px;font-weight:700;letter-spacing:10px;padding:16px 32px;border-radius:10px;">{otp}</span>
      </div>
      <p style="color:#888;font-size:13px;">This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>
      <p style="color:#aaa;font-size:12px;text-align:center;">If you did not request this, please ignore this email.</p>
    </div>
  </body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((APP_NAME, EMAIL_USER))
    msg["To"] = to_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
            print(f"OTP email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        # Not raising so dev can proceed without email; in prod monitor this log.

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
