"""
FastAPI Application for Prescription Processing System
Provides REST API endpoints for processing prescriptions
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import io
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
API_PREFIX = os.getenv("API_PREFIX", "")

from pipeline import PrescriptionProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Prescription Processing API",
    description="API for processing and analyzing prescriptions using ML models",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Pydantic Models =====

class MedicineInfo(BaseModel):
    """Medicine information"""
    name: str = Field(..., description="Medicine name")
    dosage: Optional[str] = Field(None, description="Dosage amount")
    frequency: Optional[str] = Field(None, description="Frequency of use")
    duration: Optional[str] = Field(None, description="Duration of treatment")
    confidence: Optional[float] = Field(None, description="Extraction confidence")
    matched_from: Optional[str] = Field(None, description="Original OCR token")
    fuzzy_score: Optional[float] = Field(None, description="Fuzzy matching score")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Aspirin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration": "7 days",
                "confidence": 0.95,
                "matched_from": "Aspiri",
                "fuzzy_score": 90.5
            }
        }


class InteractionInfo(BaseModel):
    """Drug interaction information"""
    drug1: str = Field(..., description="First drug name")
    drug2: str = Field(..., description="Second drug name")
    severity: str = Field(..., description="Severity level (high/moderate/low)")
    risk_score: float = Field(..., description="Risk score (0-1)")
    description: Optional[str] = Field(None, description="Interaction description")

    class Config:
        json_schema_extra = {
            "example": {
                "drug1": "Aspirin",
                "drug2": "Ibuprofen",
                "severity": "high",
                "risk_score": 0.85,
                "description": "Increased risk of gastrointestinal bleeding"
            }
        }


class PrescriptionRequest(BaseModel):
    """Request body for text-based prescription processing"""
    prescription_text: str = Field(..., description="Prescription text to process", min_length=1)
    enable_ocr: bool = Field(False, description="Enable OCR processing")

    class Config:
        json_schema_extra = {
            "example": {
                "prescription_text": "Take Aspirin 500mg twice daily for 7 days. Metformin 1000mg once daily for 30 days.",
                "enable_ocr": False
            }
        }


class PrescriptionResponse(BaseModel):
    """Response body for prescription processing"""
    status: str = Field(..., description="Processing status (success/error)")
    medicines: List[MedicineInfo] = Field(..., description="Extracted medicines")
    interactions: Optional[List[InteractionInfo]] = Field(None, description="Detected interactions")
    total_medicines: int = Field(..., description="Total medicines found")
    total_interactions: int = Field(..., description="Total interactions found")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "medicines": [
                    {
                        "name": "Aspirin",
                        "dosage": "500mg",
                        "frequency": "twice daily",
                        "duration": "7 days",
                        "confidence": 0.95
                    }
                ],
                "interactions": [
                    {
                        "drug1": "Aspirin",
                        "drug2": "Ibuprofen",
                        "severity": "high",
                        "risk_score": 0.85,
                        "description": "Increased risk of gastrointestinal bleeding"
                    }
                ],
                "total_medicines": 1,
                "total_interactions": 0,
                "warnings": [],
                "processing_time_ms": 234.5
            }
        }


class SystemStatus(BaseModel):
    """System status information"""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="API version")
    models_available: Dict[str, bool] = Field(..., description="Available models status")
    description: str = Field(..., description="System description")


# ===== Global Variables =====

processor: Optional[PrescriptionProcessor] = None


# ===== Startup and Shutdown Events =====

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global processor
    try:
        logger.info("Initializing Prescription Processor...")
        processor = PrescriptionProcessor(enable_ocr=True)
        logger.info("Prescription Processor initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing processor: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Prescription Processing API")


# ===== Health and Status Endpoints =====

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Prescription Processing API",
        "docs": "/api/docs",
        "health": "/health",
        "status": "/status"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Prescription Processing API is running"
    }


@app.get("/status", response_model=SystemStatus, tags=["Health"])
async def get_status():
    """Get system status"""
    try:
        models_status = {
            "ocr": True,
            "ner": True,
            "correction": True,
            "validation": True,
            "interaction": True
        }
        
        return SystemStatus(
            status="operational",
            version="1.0.0",
            models_available=models_status,
            description="Prescription Processing System with 5 ML models"
        )
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Prescription Processing Endpoints =====

@app.post("/process/text", response_model=PrescriptionResponse, tags=["Processing"])
async def process_prescription_text(request: PrescriptionRequest):
    """
    Process prescription from text
    
    - **prescription_text**: Prescription text to process
    - **enable_ocr**: Optional OCR processing
    
    Returns prescription analysis with medicines and interactions
    """
    if processor is None:
        logger.error("Processor not initialized")
        raise HTTPException(status_code=500, detail="Processor not initialized")
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Processing prescription text: {request.prescription_text[:100]}...")
        
        result = processor.process_from_text(request.prescription_text)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        # Extract data from result
        final_result = result.get("final_result", {})
        
        if final_result.get("status") == "error":
            logger.error(f"Text pipeline processing error: {final_result.get('error')}")
            raise HTTPException(status_code=500, detail=final_result.get("error", "Internal Processing Error"))
        
        medicines_data = []
        for med in final_result.get("medicines", []):
            medicines_data.append(MedicineInfo(
                name=med.get("name", "Unknown"),
                dosage=med.get("dosage"),
                frequency=med.get("frequency"),
                duration=med.get("duration"),
                confidence=med.get("confidence", 0.0),
                matched_from=med.get("matched_from"),
                fuzzy_score=med.get("fuzzy_score")
            ))
        
        interactions_data = []
        for interaction in final_result.get("interactions", []):
            interactions_data.append(InteractionInfo(
                drug1=interaction.get("drug1", "Unknown"),
                drug2=interaction.get("drug2", "Unknown"),
                severity=interaction.get("severity", "unknown"),
                risk_score=interaction.get("risk_score", 0.0),
                description=interaction.get("description")
            ))
        
        warnings = final_result.get("warnings", [])
        
        if not interactions_data:
            interactions_data = None
            
        logger.info(f"Processing completed. Found {len(medicines_data)} medicines and {len(interactions_data) if interactions_data else 0} interactions")
        
        return PrescriptionResponse(
            status="success",
            medicines=medicines_data,
            interactions=interactions_data,
            total_medicines=len(medicines_data),
            total_interactions=len(interactions_data) if interactions_data else 0,
            warnings=warnings,
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error processing prescription: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing prescription: {str(e)}")


@app.post("/process/image", response_model=PrescriptionResponse, tags=["Processing"])
async def process_prescription_image(file: UploadFile = File(...)):
    """
    Process prescription from image
    
    Upload a prescription image and get analysis with medicines and interactions
    """
    if processor is None:
        logger.error("Processor not initialized")
        raise HTTPException(status_code=500, detail="Processor not initialized")
    
    try:
        import time
        start_time = time.time()
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image file
        # Read image file
        content = await file.read()

        # Create temp directory (Windows safe)
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)

        temp_path = temp_dir / file.filename

        # Save image
        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info(f"Processing image: {file.filename}")

        # Process image
        result = processor.process_prescription_image(str(temp_path))
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        # Extract data
        final_result = result.get("final_result", {})
        
        if final_result.get("status") == "error":
            logger.error(f"Image pipeline processing error: {final_result.get('error')}")
            raise HTTPException(status_code=500, detail=final_result.get("error", "Internal Processing Error"))
        
        medicines_data = []
        for med in final_result.get("medicines", []):
            medicines_data.append(MedicineInfo(
                name=med.get("name", "Unknown"),
                dosage=med.get("dosage"),
                frequency=med.get("frequency"),
                duration=med.get("duration"),
                confidence=med.get("confidence", 0.0),
                matched_from=med.get("matched_from"),
                fuzzy_score=med.get("fuzzy_score")
            ))
        
        interactions_data = []
        for interaction in final_result.get("interactions", []):
            interactions_data.append(InteractionInfo(
                drug1=interaction.get("drug1", "Unknown"),
                drug2=interaction.get("drug2", "Unknown"),
                severity=interaction.get("severity", "unknown"),
                risk_score=interaction.get("risk_score", 0.0),
                description=interaction.get("description")
            ))
        
        warnings = final_result.get("warnings", [])
        
        if not interactions_data:
            interactions_data = None
            
        logger.info(f"Image processing completed. Found {len(medicines_data)} medicines and {len(interactions_data) if interactions_data else 0} interactions")
        
        return PrescriptionResponse(
            status="success",
            medicines=medicines_data,
            interactions=interactions_data,
            total_medicines=len(medicines_data),
            total_interactions=len(interactions_data) if interactions_data else 0,
            warnings=warnings,
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


# ===== Batch Processing Endpoints =====

class BatchPrescriptionRequest(BaseModel):
    """Request body for batch processing"""
    prescriptions: List[str] = Field(..., description="List of prescription texts")  # type: ignore

    class Config:
        json_schema_extra = {
            "example": {
                "prescriptions": [
                    "Take Aspirin 500mg twice daily for 7 days",
                    "Metformin 1000mg once daily"
                ]
            }
        }


@app.post("/process/batch", tags=["Processing"])
async def process_batch_prescriptions(request: BatchPrescriptionRequest):
    """
    Process multiple prescriptions in batch
    
    Submit multiple prescriptions and get analysis for each
    """
    if processor is None:
        raise HTTPException(status_code=500, detail="Processor not initialized")
    
    try:
        results = []
        
        for i, prescription_text in enumerate(request.prescriptions):
            try:
                result = processor.process_from_text(prescription_text)
                final_result = result.get("final_result", {})
                
                results.append({
                    "index": i,
                    "status": "success",
                    "medicines_count": len(final_result.get("medicines", [])),
                    "interactions_count": len(final_result.get("interactions", []))
                })
            except Exception as e:
                logger.error(f"Error processing batch item {i}: {str(e)}")
                results.append({
                    "index": i,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Batch processing completed. Processed {len(request.prescriptions)} prescriptions")
        
        return {
            "status": "completed",
            "total_processed": len(request.prescriptions),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error in batch processing: {str(e)}")


# ===== Error Handlers =====

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Generic exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(  
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
