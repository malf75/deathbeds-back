from sqlmodel import create_engine, Session
from setup.settings import DATABASE_URL
from typing import Annotated
from database.models import *
from fastapi import Depends

engine = create_engine(f"{DATABASE_URL}", echo=True)

SessionLocal = Session(autocommit=False, autoflush=False, bind=engine)

def get_db():
    with Session(engine) as session:
        yield session
        
db_dependency = Annotated[Session, Depends(get_db)] 