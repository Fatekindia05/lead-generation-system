from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
from typing import Optional
import os
import io

from models import LeadForm, LeadResponse
from mongodb_service import (
    save_lead, 
    get_all_leads, 
    get_leads_statistics,
    get_image,
    delete_image
)
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
    return {
        "status": "ok",
        "service": "FATEK Lead Generation System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/leads", response_model=LeadResponse)
async def submit_lead(lead: LeadForm):
    try:
        lead_id = save_lead(lead.model_dump())
        return LeadResponse(
            id=lead_id,
            message=f"Thank you {lead.name}! Your enquiry has been received.",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {str(e)}")


@app.get("/api/mongodb-status")
async def mongodb_status():
    """Check MongoDB connection status"""
    from mongodb_service import check_connection, get_leads_statistics
    status = {
        "connected": check_connection(),
        "stats": get_leads_statistics() if check_connection() else None,
        "message": "Connected to MongoDB" if check_connection() else "Failed to connect to MongoDB"
    }
    return status
@app.get("/api/leads")
async def get_leads(
    status: Optional[str] = None,
    requirement_type: Optional[str] = None,
    customer_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
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
    return get_leads_statistics()

@app.get("/api/images/{image_id}")
async def get_image_by_id(image_id: str):
    """Serve captured images from MongoDB"""
    try:
        image_file = get_image(image_id)
        if image_file:
            image_data = image_file.read()
            return StreamingResponse(
                io.BytesIO(image_data),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename={image_file.filename}",
                    "Cache-Control": "public, max-age=31536000"
                }
            )
    except Exception as e:
        print(f"Error serving image: {e}")
    
    raise HTTPException(status_code=404, detail="Image not found")

@app.delete("/api/images/{image_id}")
async def delete_image_by_id(image_id: str):
    """Delete image from MongoDB"""
    success = delete_image(image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "success", "message": "Image deleted"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)