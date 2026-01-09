from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin_routes import adminRouter
from app.db.session import engine
from app.db import models
from backend.app.utils import create_default_admin
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_default_admin()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(adminRouter)
