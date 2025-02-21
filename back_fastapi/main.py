import asyncio
import boto3
import smtplib
from email.mime.text import MIMEText
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, UploadFile, Depends, HTTPException, Form, BackgroundTasks, Cookie
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from .database import AsyncSessionLocal
from .users_repository import UsersRepository
from .clothes_repository import ClothesRepository

# Initialize repositories
users_repo = UsersRepository()
clothes_repo = ClothesRepository()

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 Config (Load these from environment variables in production)
S3_BUCKET_NAME = "***"
S3_ACCESS_KEY_ID = "***"
S3_SECRET_ACCESS_KEY = "***"

COOKIE_MAX_AGE = 3600

# Async DB Dependency
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

# JWT Handling with Cache
@lru_cache(maxsize=1000)
def decode_jwt(token: str) -> int:
    """Decode JWT and return user ID."""
    data = jwt.decode(token, "secret_key", "HS256")
    return data['user_id']

def create_jwt(user_id: int) -> str:
    """Create JWT token."""
    return jwt.encode({'user_id': user_id}, "secret_key", "HS256")

# Async Email Sending
async def send_email_async(email: str, otp: str):
    sender = "your-email@example.com"
    password = "your-email-password"

    msg = MIMEText(f"Your OTP code is {otp}. It is valid for 10 minutes.")
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = sender
    msg["To"] = email

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_email_sync, sender, password, email, msg)

def send_email_sync(sender, password, recipient, msg):
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

@app.post("/api/forgot-password")
async def forgot_password(email: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await users_repo.get_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist.")
    
    otp_code = str(random.randint(100000, 999999))
    # Store OTP asynchronously
    await otp_repo.create_otp(db, {"otp_code": otp_code, "user_id": user.id, "email": email})

    # Send email in the background
    background_tasks.add_task(send_email_async, email, otp_code)
    return {"detail": "OTP has been sent to your email."}

@app.post("/api/upload")
async def add_photo(
    file: UploadFile,
    name: str = Form(...),
    category: str = Form(...),
    token: str = Cookie(),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a file asynchronously to S3 and stores metadata."""
    user_id = decode_jwt(token)

    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    )

    file_key = f"{user_id}/{file.filename}"

    # Asynchronous file upload
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: s3.upload_fileobj(
        file.file, S3_BUCKET_NAME, file_key, ExtraArgs={"ACL": "public-read", "ContentType": file.content_type}
    ))

    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file_key}"

    clothes_data = {
        "name": name,
        "category": category,
        "user_id": user_id,
        "url": uploaded_file_url
    }

    created_clothes = await clothes_repo.create_clothes(db, clothes_data)
    return {"file": file.filename, "clothes": created_clothes}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
