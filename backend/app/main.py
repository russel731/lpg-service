from fastapi import FastAPI
from app.database import engine, Base
from app.models import OwnerRequest
from app.routers.owner import router as owner_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(owner_router)


@app.get("/")
def root():
    return {"status": "ok"}