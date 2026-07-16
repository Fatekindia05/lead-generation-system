import json
import os
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any

LEADS_FILE = "data/leads.json"
IMAGES_DIR = "data/images"

def init_leads_file():
    """Initialize leads.json if it doesn't exist"""
    os.makedirs(os.path.dirname(LEADS_FILE), exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    if not os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'w') as f:
            json.dump([], f, indent=2)
        print(f"✅ Created new leads file at {LEADS_FILE}")

def save_image(base64_data, lead_id):
    """Save base64 image to file"""
    if not base64_data:
        print("⚠️ No image data to save")
        return None
        
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Generate filename
        filename = f"visitor_{lead_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ Image saved: {filepath}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save image: {e}")
        return None

def get_next_id(leads):
    """Get next available ID for new lead"""
    if not leads:
        return 1
    return max(lead.get('id', 0) for lead in leads) + 1

def save_lead(lead_data: Dict[str, Any]) -> int:
    """Save lead to JSON file with proper structure"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        leads = []
    
    lead_id = get_next_id(leads)
    
    # Save image if provided
    image_filename = None
    if lead_data.get('image_url'):
        print(f"📸 Saving image for lead {lead_id}...")
        image_filename = save_image(lead_data['image_url'], lead_id)
    else:
        print("⚠️ No image_url in lead data")
    
    # Create lead entry
    lead_entry = {
        "id": lead_id,
        "name": lead_data.get("name", ""),
        "company": lead_data.get("company", ""),
        "email": lead_data.get("email", ""),
        "phone": lead_data.get("phone", ""),
        "requirement_type": lead_data.get("requirement_type", ""),
        "customer_type": lead_data.get("customer_type", ""),
        "other_customer_type": lead_data.get("other_customer_type", None),
        "message": lead_data.get("message", ""),
        "source": lead_data.get("source", "web_form"),
        "image_url": f"/api/images/{image_filename}" if image_filename else None,
        "status": "new",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    leads.append(lead_entry)
    
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"✅ Lead saved with ID: {lead_entry['id']}")
    print(f"📸 Image URL: {lead_entry['image_url']}")
    return lead_entry['id']

def get_all_leads(
    status: Optional[str] = None,
    requirement_type: Optional[str] = None,
    customer_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get all leads with filters"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    
    filtered_leads = []
    for lead in leads:
        if status and lead.get('status') != status:
            continue
        
        if requirement_type and lead.get('requirement_type') != requirement_type:
            continue
        
        if customer_type and lead.get('customer_type') != customer_type:
            continue
        
        if date_from or date_to:
            try:
                created_at = datetime.fromisoformat(lead.get('created_at', '2000-01-01'))
                if date_from and created_at < date_from:
                    continue
                if date_to and created_at > date_to:
                    continue
            except (ValueError, TypeError):
                pass
        
        if search:
            search_lower = search.lower()
            lead_text = f"{lead.get('name', '')} {lead.get('email', '')} {lead.get('company', '')}".lower()
            if search_lower not in lead_text:
                continue
        
        filtered_leads.append(lead)
    
    filtered_leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return filtered_leads[offset:offset + limit]

def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """Get single lead by ID"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
        
        for lead in leads:
            if lead.get('id') == lead_id:
                return lead
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return None

def update_lead_status(lead_id: int, status: str) -> bool:
    """Update lead status"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
        
        updated = False
        for lead in leads:
            if lead.get('id') == lead_id:
                lead['status'] = status
                lead['updated_at'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            with open(LEADS_FILE, 'w') as f:
                json.dump(leads, f, indent=2)
            print(f"✅ Lead {lead_id} status updated to: {status}")
            return True
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return False

def get_leads_statistics() -> Dict:
    """Get statistics about leads"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        leads = []
    
    today = datetime.now().date()
    
    stats = {
        "total_leads": len(leads),
        "new_count": len([l for l in leads if l.get('status') == 'new']),
        "contacted_count": len([l for l in leads if l.get('status') == 'contacted']),
        "converted_count": len([l for l in leads if l.get('status') == 'converted']),
        "closed_count": len([l for l in leads if l.get('status') == 'closed']),
        "today_leads": len([l for l in leads if 
                           l.get('created_at') and 
                           datetime.fromisoformat(l['created_at']).date() == today]),
        "with_images": len([l for l in leads if l.get('image_url')]),
        "requirement_counts": {},
        "customer_type_counts": {}
    }
    
    for lead in leads:
        req = lead.get('requirement_type', 'Unknown')
        stats["requirement_counts"][req] = stats["requirement_counts"].get(req, 0) + 1
        
        cust = lead.get('customer_type', 'Unknown')
        stats["customer_type_counts"][cust] = stats["customer_type_counts"].get(cust, 0) + 1
    
    return stats

def delete_lead(lead_id: int) -> bool:
    """Delete lead by ID"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)
        
        for lead in leads:
            if lead.get('id') == lead_id and lead.get('image_url'):
                image_filename = lead['image_url'].split('/')[-1]
                image_path = os.path.join(IMAGES_DIR, image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"🗑️ Deleted image: {image_path}")
                break
        
        new_leads = [lead for lead in leads if lead.get('id') != lead_id]
        
        if len(new_leads) < len(leads):
            with open(LEADS_FILE, 'w') as f:
                json.dump(new_leads, f, indent=2)
            print(f"✅ Lead {lead_id} deleted")
            return True
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return False

def export_leads() -> List[Dict]:
    """Export all leads for download"""
    init_leads_file()
    
    try:
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []