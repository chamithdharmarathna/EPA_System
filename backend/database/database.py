from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
import time

os.makedirs("data", exist_ok=True)

# Use timeout and proper settings for SQLite
DATABASE_URL = "sqlite:///./data/epa_system.db?check_same_thread=False&timeout=30"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "timeout": 30,  # Wait 30 seconds for lock to clear
        "check_same_thread": False
    },
    pool_size=5,  # Only 1 connection for SQLite
    max_overflow=10,  # No overflow connections
    pool_timeout=60,
    echo=False
)

# Use scoped_session for thread safety
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def init_db():
    retries = 3
    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database initialized at ./data/epa_system.db")
            break
        except Exception as e:
            if i < retries - 1:
                print(f"Database init failed, retrying... ({i+1}/{retries})")
                time.sleep(1)
            else:
                print(f"Database init failed: {e}")
                raise