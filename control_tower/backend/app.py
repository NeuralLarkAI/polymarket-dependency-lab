from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.runs import router as runs_router
from api.control import router as control_router

app = FastAPI(title="Control Tower Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(runs_router, prefix="/api")
app.include_router(control_router, prefix="/api")
