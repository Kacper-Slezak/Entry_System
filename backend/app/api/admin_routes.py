from fastapi import APIRouter


adminRouter = APIRouter(prefix="/admin", tags=["health"])

@adminRouter.get("/health")
async def health_check():
    return {200: "OK"}