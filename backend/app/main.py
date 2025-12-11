from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin_routes import adminRouter
from app.db.session import engine
from app.db import models

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(adminRouter)
