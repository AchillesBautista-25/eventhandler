import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///eventhandler.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:3000/auth/callback")

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # set True in production (HTTPS)

    PORT = int(os.getenv("PORT", 3000))