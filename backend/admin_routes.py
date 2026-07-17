from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import io
import csv
import base64
from datetime import datetime
import os
import tempfile
import shutil

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image

from models import LeadUpdate, LeadsFilter
from lead_service import (
    get_all_leads,
    get_lead_by_id,
    update_lead_status,
    get_leads_statistics,
    delete_lead,
    export_leads
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/leads")
async def get_leads(
    status: Optional[str] = Query(None, description="Filter by status"),
    requirement_type: Optional[str] = Query(None, description="Filter by requirement type"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type"),
    search: Optional[str] = Query(None, description="Search in name, email, company"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all leads with filters"""
    leads = get_all_leads(
        status=status,
        requirement_type=requirement_type,
        customer_type=customer_type,
        search=search,
        limit=limit,
        offset=offset
    )
    return {"leads": leads, "total": len(leads)}

@router.get("/leads/{lead_id}")
async def get_lead(lead_id: int):
    """Get lead by ID"""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.patch("/leads/{lead_id}/status")
async def update_lead(lead_id: int, update: LeadUpdate):
    """Update lead status"""
    success = update_lead_status(lead_id, update.status)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "success", "message": f"Lead {lead_id} updated to {update.status}"}

@router.delete("/leads/{lead_id}")
async def remove_lead(lead_id: int):
    """Delete lead by ID"""
    success = delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "success", "message": f"Lead {lead_id} deleted"}

@router.get("/stats")
async def get_stats():
    """Get lead statistics"""
    return get_leads_statistics()

@router.get("/export/csv")
async def export_csv():
    """Export leads as CSV"""
    leads = export_leads()
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads to export")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ["ID", "Name", "Company", "Email", "Phone", "Requirement Type", 
               "Customer Type", "Other Customer Type", "Status", "Created At", "Message"]
    writer.writerow(headers)
    
    for lead in leads:
        writer.writerow([
            lead.get('id'),
            lead.get('name'),
            lead.get('company'),
            lead.get('email'),
            lead.get('phone'),
            lead.get('requirement_type'),
            lead.get('customer_type'),
            lead.get('other_customer_type', ''),
            lead.get('status'),
            lead.get('created_at'),
            lead.get('message', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/export/excel")
async def export_excel():
    """
    Export leads as Excel file with embedded high-quality images
    Images are embedded at a higher resolution for better quality
    """
    leads = export_leads()
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads to export")
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"
    
    # Define styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    wrap_alignment = Alignment(wrap_text=True, vertical="top")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # Headers with Image column
    headers = ["ID", "Image", "Name", "Company", "Email", "Phone", 
               "Requirement Type", "Customer Type", "Other Customer Type", 
               "Status", "Created At", "Message"]
    
    # Column widths - wider for image column
    col_widths = [6, 35, 20, 25, 30, 15, 20, 18, 20, 12, 22, 50]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        ws.column_dimensions[get_column_letter(col)].width = col_widths[col-1]
    
    ws.row_dimensions[1].height = 30
    
    # Track rows with images
    image_rows = {}
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        for row_idx, lead in enumerate(leads, 2):
            # ID
            ws.cell(row=row_idx, column=1, value=lead.get('id'))
            ws.cell(row=row_idx, column=1).alignment = center_alignment
            
            # Image - insert into cell with HIGH quality
            image_url = lead.get('image_url')
            if image_url:
                try:
                    filename = image_url.split('/')[-1]
                    image_path = os.path.join("data/images", filename)
                    
                    if os.path.exists(image_path):
                        # Open and resize image - BETTER QUALITY
                        with Image.open(image_path) as img:
                            # Convert to RGB if necessary
                            if img.mode in ('RGBA', 'LA', 'P'):
                                img = img.convert('RGB')
                            
                            # Calculate new size - larger for better quality
                            # Max 300x240 pixels for better visibility
                            max_width = 300
                            max_height = 240
                            
                            # Calculate aspect ratio
                            width_ratio = max_width / img.width
                            height_ratio = max_height / img.height
                            ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
                            
                            new_width = int(img.width * ratio)
                            new_height = int(img.height * ratio)
                            
                            # Resize using LANCZOS (highest quality)
                            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            
                            # Save to temp file with HIGH quality
                            temp_path = os.path.join(temp_dir, f"img_{row_idx}.jpg")
                            img_resized.save(temp_path, 'JPEG', quality=95, optimize=True)
                            temp_files.append(temp_path)
                            
                            # Add to Excel with original size (not scaled by Excel)
                            xl_img = XLImage(temp_path)
                            # Calculate Excel dimensions (1 unit ≈ 7 pixels)
                            # This ensures the image displays at the correct size
                            xl_img.width = new_width
                            xl_img.height = new_height
                            
                            cell_ref = f'B{row_idx}'
                            ws.add_image(xl_img, cell_ref)
                            
                            # Store row height - make it tall enough for the image
                            image_rows[row_idx] = max(120, new_height // 7 + 10)
                    else:
                        ws.cell(row=row_idx, column=2, value="Image not found")
                        ws.cell(row=row_idx, column=2).alignment = center_alignment
                except Exception as e:
                    print(f"Error adding image for lead {lead.get('id')}: {e}")
                    ws.cell(row=row_idx, column=2, value="Image Error")
                    ws.cell(row=row_idx, column=2).alignment = center_alignment
            else:
                ws.cell(row=row_idx, column=2, value="No Image")
                ws.cell(row=row_idx, column=2).alignment = center_alignment
            
            # Other fields
            ws.cell(row=row_idx, column=3, value=lead.get('name'))
            ws.cell(row=row_idx, column=4, value=lead.get('company'))
            ws.cell(row=row_idx, column=5, value=lead.get('email'))
            ws.cell(row=row_idx, column=6, value=lead.get('phone', ''))
            ws.cell(row=row_idx, column=7, value=lead.get('requirement_type'))
            ws.cell(row=row_idx, column=8, value=lead.get('customer_type'))
            ws.cell(row=row_idx, column=9, value=lead.get('other_customer_type', ''))
            ws.cell(row=row_idx, column=10, value=lead.get('status'))
            ws.cell(row=row_idx, column=11, value=lead.get('created_at'))
            ws.cell(row=row_idx, column=12, value=lead.get('message', ''))
            ws.cell(row=row_idx, column=12).alignment = wrap_alignment
        
        # Apply row heights for rows with images
        for row_idx, height in image_rows.items():
            ws.row_dimensions[row_idx].height = height
        
        # Save to memory
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=leads_with_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    
    finally:
        # Clean up temp directory and files
        shutil.rmtree(temp_dir, ignore_errors=True)