from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
from typing import Optional
import os

from models import LeadForm, LeadResponse
from lead_service import save_lead, get_all_leads, get_leads_statistics
from admin_routes import router as admin_router

app = FastAPI(
    title="FATEK Lead Generation System",
    description="Lead capture and management system for FATEK Automation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "https://*.netlify.app",
        "https://*.vercel.app",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin routes
app.include_router(admin_router)

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FATEK Lead Generation System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "submit_lead": "/api/leads",
            "admin_dashboard": "/api/admin",
            "stats": "/api/admin/stats"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "FATEK Lead Generation System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/leads", response_model=LeadResponse)
async def submit_lead(lead: LeadForm):
    """Submit a new lead"""
    try:
        lead_id = save_lead(lead.model_dump())
        
        return LeadResponse(
            id=lead_id,
            message=f"Thank you {lead.name}! Your enquiry has been received. Our team will contact you soon.",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {str(e)}")

@app.get("/api/leads")
async def get_leads(
    status: Optional[str] = None,
    requirement_type: Optional[str] = None,
    customer_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get all leads with optional filters"""
    leads = get_all_leads(
        status=status,
        requirement_type=requirement_type,
        customer_type=customer_type,
        search=search,
        limit=limit,
        offset=offset
    )
    return {"leads": leads, "count": len(leads)}

@app.get("/api/stats")
async def get_stats():
    """Get lead statistics"""
    return get_leads_statistics()

@app.get("/api/images/{image_filename}")
async def get_image(image_filename: str):
    """Serve captured images"""
    image_path = os.path.join("data/images", image_filename)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)