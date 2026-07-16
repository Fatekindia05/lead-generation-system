from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import io
import csv
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ["ID", "Name", "Company", "Email", "Phone", "Requirement Type", 
               "Customer Type", "Other Customer Type", "Status", "Created At", "Message"]
    writer.writerow(headers)
    
    # Write data
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
    """Export leads as Excel file"""
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
    header_alignment = Alignment(horizontal="center")
    
    # Write headers
    headers = ["ID", "Name", "Company", "Email", "Phone", "Requirement Type", 
               "Customer Type", "Other Customer Type", "Status", "Created At", "Message"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Write data
    for row, lead in enumerate(leads, 2):
        ws.cell(row=row, column=1, value=lead.get('id'))
        ws.cell(row=row, column=2, value=lead.get('name'))
        ws.cell(row=row, column=3, value=lead.get('company'))
        ws.cell(row=row, column=4, value=lead.get('email'))
        ws.cell(row=row, column=5, value=lead.get('phone'))
        ws.cell(row=row, column=6, value=lead.get('requirement_type'))
        ws.cell(row=row, column=7, value=lead.get('customer_type'))
        ws.cell(row=row, column=8, value=lead.get('other_customer_type', ''))
        ws.cell(row=row, column=9, value=lead.get('status'))
        ws.cell(row=row, column=10, value=lead.get('created_at'))
        ws.cell(row=row, column=11, value=lead.get('message', ''))
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )