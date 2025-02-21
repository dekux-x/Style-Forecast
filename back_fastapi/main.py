import boto3
# import psycopg2
from sqlalchemy.orm import Session

from back_fastapi.est_algorithm import get_recommendations
from .database import Base, engine, SessionLocal
from .users_repository import *
from .clothes_repository import *
from .feedback_repository import *
from .otp_repository import *
from . algorithm import *

import random
import smtplib
from email.mime.text import MIMEText

import uvicorn
from fastapi import FastAPI, UploadFile, Depends, HTTPException, Form, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import State


from jose import jwt

Base.metadata.create_all(bind=engine)
clothes_repo = ClothesRepository()
users_repo = UsersRepository()
feedback_repo = FeedbackRepository()
otp_repo = OTPRepository()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081" ],  # Change "*" to specific origins like ["http://localhost:8081"] in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow specific headers
)


S3_BUCKET_NAME = "***"
S3_ACCESS_KEY_ID="***"
S3_SECRET_ACCESS_KEY="***"

COOKIE_MAX_AGE = 3600

class MaxRequestSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if "content-length" in request.headers:
            content_length = int(request.headers["content-length"])
            if content_length > 10 * 1024 * 1024:  # Лимит: 50 МБ
                return Response("Request too large", status_code=413)
        return await call_next(request)

app.add_middleware(MaxRequestSizeMiddleware)

def get_db():
    db= SessionLocal()
    try:
        yield db 
    finally:
        db.close()

def create_jwt(user_id: int)->str:
    body = {'user_id': user_id}
    token = jwt.encode(body,"Adilzhan-Dias-Alikhan-Olzhas-Adilkhan-SF-secret","HS256")
    return token

def decode_jwt(token:str)->int:
    data = jwt.decode(token,"Adilzhan-Dias-Alikhan-Olzhas-Adilkhan-SF-secret","HS256")
    return data['user_id']


def send_email(email: str, otp: str):
    sender = ""
    password = ""

    msg = MIMEText(f"Your OTP code is {otp}. It is valid for 10 minutes.")
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = sender
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())


@app.get("/api/clothes/{clothes_id}")
def get_clothes_by_id(clothes_id: int,db: Session = Depends(get_db)) -> ClothingsResponse:
    clothes = clothes_repo.get_clothes_by_id(db,clothes_id)
    return clothes

@app.get("/api/recomendation")
def get_recommendation(t: int, token: str = Cookie(),db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    clothes = clothes_repo.get_clothes(db,user_id)
    user = users_repo.get_by_id(db,user_id)
    schemas = [ClothingsResponse.from_orm(item) for item in clothes]
    weight = user.weight
    # warmness_class = weather_fun(t, weight)
    #
    # graph = build_graph(schemas)
    # paths = find_top_n_paths(graph, schemas, ["Shirts", "Pants", "Shoes"], 5)
    paths = get_recommendations(temperature=t, weight=weight, wardrobe=schemas)
    return paths
    

@app.get('/api/clothes')
def get_clothes(db: Session = Depends(get_db))-> list[ClothingsResponse]:
    clothes = clothes_repo.get_clothes(db,0)
    return clothes

@app.get('/api/my_clothes')
def get_my_clothes( token: str=Cookie(), db: Session = Depends(get_db))-> list[ClothingsResponse]:
    user_id = decode_jwt(token)
    clothes = clothes_repo.get_clothes(db,user_id)
    return clothes

@app.delete('/api/clothes/{clothes_id}')
def del_clothes_by_id(clothes_id: int, token: str=Cookie(),db: Session=Depends(get_db)):
    user_id = decode_jwt(token)
    deleted = clothes_repo.delete_clothes(db,clothes_id,user_id)
    if deleted is None:
        raise HTTPException(status_code = 404, detail = "There is no such clothes")
    elif not deleted:
        raise HTTPException(status_code = 403, detail = "You don't have the right")
    return Response(status_code=204)

@app.put("/api/clothes/{clothes_id}")
def update_clothes(clothes_id: int, clothes: ClothingsRequest, token: str = Cookie(), db: Session = Depends(get_db)) -> ClothingsResponse:
    update_data = clothes.dict()
    update_data['user_id'] = decode_jwt(token)
    del update_data['url']
    updated_model = clothes_repo.update_clothes(db,clothes_id,update_data)
    if updated_model is None:
        raise HTTPException(status_code = 404, detail = "There is no such clothes")
    elif not updated_model:
        raise HTTPException(status_code = 403, detail = "You don't have the right")
    return updated_model

@app.post("/api/clothes", status_code = 201)
async def add_photo(file: UploadFile,
                    name: str = Form(...),
                    category: str = Form(...),
                    subcategory: str = Form(...),
                    warmness: str = Form(...),
                    color: str = Form(...),
                    token: str = Cookie(),
                    db: Session = Depends(get_db)):
    # #Upload file to AWS S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    )
    # s3.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename)
    s3.upload_fileobj(
        file.file,
        S3_BUCKET_NAME,
        file.filename,
        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type}
    )
    # bucket = s3.Bucket(S3_BUCKET_NAME)
    # bucket.upload_fileobj(file.file, file.filename, ExtraArgs={"ACL": "public-read"})

    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
    
    try:
        user_id = decode_jwt(token)
        clothes = ClothingsRequest(
            name=name,
            category = category,
            subcategory = subcategory,
            warmness = warmness,
            color=color,
        )
        create_data = clothes.dict()
        create_data['user_id'] = user_id
        create_data['url'] = uploaded_file_url
        
    except Exception as e:
        raise HTTPException(status_code = 400, detail = str(e)) 
    clothes.url = file.filename + "url1234"
    created_clothes = clothes_repo.create_clothes(db,clothes=create_data)
    return {"file": file.filename,"clothes": created_clothes}

@app.post("/api/register", status_code=201)
def register_user(user: UsersSchema, db: Session = Depends(get_db)):
    if users_repo.get_by_username(db, user.username) or users_repo.get_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="User with this username or email already exists")
    
    new_user = users_repo.create(db,user)
    token = create_jwt(new_user.id)
    response = Response("user saccessfully registered", status_code = 201)
    response.set_cookie(
        key="token",
        value=token,
        max_age=COOKIE_MAX_AGE,  # Expiration in seconds
        httponly=True,  # Secure cookie (not accessible via JavaScript)
        secure=False,  # Установить True на продакшене
        samesite="None",
    )
    return response

@app.post("/api/login")
def login_user(user: UserRequest, db: Session = Depends(get_db)):
    user_db = users_repo.get_by_username(db,user.username)
    if not user_db:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    if user_db.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_jwt(user_db.id)
    response = Response("User Successfully Logged In", status_code = 200)
    response.set_cookie(
        key="token",
        value=token,
        max_age=COOKIE_MAX_AGE,  # Expiration in seconds
        httponly=True,  # Secure cookie (not accessible via JavaScript)
        secure=True,  # Установить True на продакшене
        samesite="None",
    )
    return response

@app.get("/api/profile")
def get_user(token: str = Cookie(), db: Session = Depends(get_db))-> UserResponse:
    user_id = decode_jwt(token)
    user_db = users_repo.get_by_id(db,user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="There is no such user")

    return user_db

@app.post("/api/change_password")
def change_password(values: ChangePassword, token: str = Cookie(),db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    user = users_repo.get_by_id(db,user_id)
    if user.password == values.old_password:
        user = users_repo.update_password(db,user,values.new_password)
        response = Response("Password changed", status_code = 200)
        return response
    return HTTPException(status_code = 400,detail = "Wrong password")


@app.post("/api/feedback", response_model=FeedbackResponse)
def create_feedback(feedback: FeedbackRequest, token: str = Cookie(),db: Session = Depends(get_db), ):
    feedback_data = feedback.dict()
    feedback_data["user_id"] = decode_jwt(token)
    return feedback_repo.create_feedback(db, feedback_data)

@app.get("/api/feedback", response_model=list[FeedbackResponse])
def get_feedback(db: Session = Depends(get_db)):
    return feedback_repo.get_feedbacks(db)


@app.post("/api/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = users_repo.get_by_email(db,email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist.")
    otp_code = str(random.randint(100000, 999999))
    otp_repo.create_otp(db,{"otp_code": otp_code,"user_id": user.id, 'email': email})
    send_email(email, otp_code)
    return {"detail": "OTP has been sent to your email."}

@app.post("/api/verify-otp")
def verify_otp(otp: OTPRequest, db: Session = Depends(get_db)):
    otp_entry = otp_repo.get_otp_by_email(db,otp.email)
    print(otp_entry)
    print(otp_entry.otp_code)
    print(otp.content)

    if not otp_entry or otp_entry.otp_code != otp.content:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    if not otp_entry.is_valid():
        raise HTTPException(status_code=400, detail="OTP has expired.")

    user_db = users_repo.get_by_email(db,otp.email)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found.")
    
    token = create_jwt(user_db.id)
    response = Response("User Successfully Authorized", status_code = 200)
    response.set_cookie(
        key="token",
        value=token,
        max_age=COOKIE_MAX_AGE,  # Expiration in seconds
        httponly=True,  # Secure cookie (not accessible via JavaScript)
        secure=False,  # Установить True на продакшене
        samesite= "lax",
    )
    return response

@app.post("/api/reset_password")
def reset_password(password: ResetPassword, token: str = Cookie(),db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    user = users_repo.get_by_id(db,user_id)
    users_repo.update_password(db,user,password.password)
    return {"detail": "Password Changed successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
