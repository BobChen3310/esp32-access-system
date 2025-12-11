from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import users, access, devices, auth, bot_api
from app.auth import get_current_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    lifespan=lifespan,
    docs_url=None,    
    redoc_url=None,   
    openapi_url=None  
)

origins = ["https://test.bob0623.net", "http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(access.router)
app.include_router(bot_api.router)
app.include_router(users.router, dependencies=[Depends(get_current_admin)])
app.include_router(devices.router, dependencies=[Depends(get_current_admin)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
