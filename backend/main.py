"""
KLFINAL Backend API
FastAPI service exposing model inference, health check, and lottery lists.
"""

from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import os
import re
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from prediction import service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models once at application startup
    print("[Startup] Initializing and preloading KL1 and KLED2 lottery models...")
    try:
        service.load_models()
        print("[Startup] Models loaded and ready to serve predictions.")
    except Exception as e:
        print(f"[Startup ERROR] Failed to load models: {e}")
    yield
    print("[Shutdown] Cleaning up application resources.")


app = FastAPI(
    title="KLFINAL - Dual Machine Learning Lottery Prediction API",
    description="High-performance ML prediction engine powered by KL1 and KLED2 models for Kerala Lottery analysis.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Netlify frontend and local development
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.netlify.app",
    "*"  # Allows all origins for seamless production deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Netlify and local preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    date: str = Field(
        ...,
        description="Lottery draw date in YYYY-MM-DD format",
        example="2026-11-15"
    )
    lottery: str = Field(
        ...,
        description="Name of the Kerala Lottery",
        example="Karunya"
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v.strip()):
            raise ValueError("Date must be formatted as YYYY-MM-DD")
        return v.strip()

    @field_validator("lottery")
    @classmethod
    def validate_lottery_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Lottery name cannot be empty")
        return v.strip()


class KL1Candidate(BaseModel):
    rank: int
    candidate: str
    score: float


class KL1Result(BaseModel):
    candidates: List[KL1Candidate]


class KLED2Result(BaseModel):
    prediction: str


class PredictionResponse(BaseModel):
    success: bool
    date: str
    lottery: str
    kl1: KL1Result
    kled2: KLED2Result


@app.get("/")
def root():
    return {
        "app": "KLFINAL",
        "description": "Dual Machine Learning Prediction System API",
        "status": "online",
        "endpoints": {
            "health": "/api/health",
            "lotteries": "/api/lotteries",
            "predict": "/api/predict"
        }
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint indicating model load status."""
    return {
        "status": "healthy",
        "models_loaded": service._is_loaded,
        "lotteries_count": len(service.lottery_names)
    }


@app.get("/api/lotteries")
def get_lotteries():
    """Returns the list of valid Kerala Lottery names."""
    if not service._is_loaded:
        try:
            service.load_models()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Models are not yet loaded: {str(e)}"
            )

    return {
        "success": True,
        "count": len(service.lottery_names),
        "lotteries": service.lottery_names
    }


@app.post("/api/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    """
    Predicts lottery results using both KL1 and KLED2 models for the same date and lottery.
    """
    if not service._is_loaded:
        try:
            service.load_models()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model engine is currently initializing or unavailable: {str(e)}"
            )

    try:
        results = service.predict(payload.date, payload.lottery)
        return results
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(err)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
