from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

pwt_context= CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY="your-secret-key-change-this-later"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

def hash_password(password:str):
    return pwt_context.hash(password)

def verify_password(plain_password:str, hashed_password:str):
    return pwt_context.verify(plain_password, hashed_password)

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token:str=Depends(oauth2_scheme)):
    credentials_exception=HTTPException(
        status_code=401,
        detail="認証所法が無効です",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str=payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
    
