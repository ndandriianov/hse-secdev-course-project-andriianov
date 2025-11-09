import os
import time
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./okr.db")
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    for _ in range(10):
        try:
            SQLModel.metadata.create_all(engine)
            print("Database connected and tables created.")
            break
        except OperationalError:
            print("Database not ready, retrying...")
            time.sleep(2)

def get_session():
    with Session(engine) as session:
        yield session