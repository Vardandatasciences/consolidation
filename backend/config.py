import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class - All values from .env file"""
    
    # Database Configuration - REQUIRED from .env
    DB_HOST = os.getenv('DB_HOST')
    if not DB_HOST:
        raise ValueError("DB_HOST environment variable is required. Please set it in .env file.")
    
    DB_USER = os.getenv('DB_USER')
    if not DB_USER:
        raise ValueError("DB_USER environment variable is required. Please set it in .env file.")
    
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD environment variable is required. Please set it in .env file.")
    
    DB_NAME = os.getenv('DB_NAME')
    if not DB_NAME:
        raise ValueError("DB_NAME environment variable is required. Please set it in .env file.")
    
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
    DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '10'))
    
    # Flask Configuration - REQUIRED from .env
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required. Please set it in .env file.")
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is required. Please set it in .env file.")
    
    # Server Configuration
    PORT = int(os.getenv('PORT', '5000'))
    
    # CORS Configuration
    # Allow CORS origins from environment variable (comma-separated) or use defaults
    cors_origins_env = os.getenv('CORS_ORIGINS', '')
    if cors_origins_env:
        CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    else:
        # Default CORS origins if not specified in .env
        CORS_ORIGINS = [
            "http://localhost:5173", 
            "http://localhost:3000", 
            "http://localhost:8080",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "http://13.203.205.180",
            "http://finance.vardaands.com"
        ]

