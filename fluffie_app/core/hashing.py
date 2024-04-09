from passlib.context import CryptContext
from datetime import datetime, timedelta
from .config import JWT_TOKEN_PREFIX, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hasher():
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(*, data: dict, expires_delta: int = None):
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "sub": "access"})
        encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)

        return encoded_jwt