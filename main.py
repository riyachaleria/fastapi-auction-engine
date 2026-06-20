"""
Entry point for the BidBazaar FastAPI application.
Configures lifespan events, global exception handlers, and includes API routers.
"""
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from routes import auth, items, websockets
from exceptions import global_exception_handler, HTTP_exception_handler
from scheduler import scheduler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of the FastAPI application.
    Starts the APScheduler on startup and shuts it down cleanly on shutdown.
    
    Args:
        app (FastAPI): The running FastAPI instance.
    """
    scheduler.start()
    print("Background Scheduler is ALIVE!")

    yield

    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, HTTP_exception_handler)

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(websockets.router)