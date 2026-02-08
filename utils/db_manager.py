import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.models import Base

# Load environment variables (dotenv is optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed - use system env or Streamlit secrets
    pass

# Get DB URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Singleton engine
_message_printed = False
# _message_printed = False
# _engine = None

@st.cache_resource
def get_db_engine():
    """
    Get SQLAlchemy engine (Singleton via Streamlit Cache)
    """
    
    # if not DATABASE_URL:
    #     if not _message_printed:
    #         print("Warning: DATABASE_URL not found in environment variables.")
    #         _message_printed = True
    #     return None
        
    # if _engine is not None:
    #     return _engine
    
    # Increase pool limits to prevent blocking under load
    try:
        # Use singleton engine to prevent connection exhaustion AND enable pooling for speed
        _engine = create_engine(
            DATABASE_URL, 
            echo=False, 
            pool_size=10,        # Increased from 2 to 10
            max_overflow=20,     # Allow burst
            pool_timeout=30,     # Wait 30s before giving up
            pool_recycle=1800,   # Recycle every 30 mins
            pool_pre_ping=True   # Check connection validity before use
        )
        return _engine
    except Exception as e:
        print(f"Error creating DB engine: {e}")
        return None

def init_db():
    """Create tables if they don't exist"""
    engine = get_db_engine()
    if engine:
        print(f"Connecting to database at {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '...'}")
        Base.metadata.create_all(engine)
        print("Database initialized successfully (Tables created/verified).")
    else:
        print("Failed to initialize database: No Engine.")

if __name__ == "__main__":
    # Allow running this file directly to init DB
    init_db()
