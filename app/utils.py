from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(plain_text: str):
    return pwd_context.hash(plain_text)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
