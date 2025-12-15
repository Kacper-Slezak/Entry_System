from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin_routes import adminRouter
from app.db.session import engine
from app.db import models

from dotenv import load_dotenv

from backend.app.core.security import get_password_hash
from backend.app.db.session import SessionLocal

load_dotenv()

models.Base.metadata.create_all(bind=engine)

def create_default_admin():
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).first()
        if not admin:
            print("INFO: Tworzenie domyślnego konta administratora...")
            default_admin = models.Admin(
                username = "admin",
                hashed_password = get_password_hash("admin123")
            )
            db.add(default_admin)
            db.commit()
            print("INFO: Utworzono konto administratora: admin / admin123")
    finally:
        db.close()

create_default_admin()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(adminRouter)
