import os
import base64
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
import gridfs
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://fatek_user:Fatek2026@cluster0.d5wpzja.mongodb.net/fatek_leads?appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "fatek_leads")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
leads_collection = db["leads"]
fs = gridfs.GridFS(db)

def init_db():
    """Initialize database collections and indexes"""
    # Create counters collection for auto-increment
    if db.counters.count_documents({"_id": "lead_id"}) == 0:
        db.counters.insert_one({"_id": "lead_id", "seq": 0})

def get_next_id():
    """Get next auto-increment ID"""
    counter = db.counters.find_one_and_update(
        {"_id": "lead_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]

def save_image(base64_data, lead_id):
    """Save image to GridFS and return file ID"""
    if not base64_data:
        return None
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        filename = f"visitor_{lead_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Store in GridFS
        file_id = fs.put(
            image_data,
            filename=filename,
            metadata={
                "lead_id": lead_id,
                "uploaded_at": datetime.now()
            }
        )
        print(f"✅ Image saved to MongoDB with ID: {file_id}")
        return str(file_id)
    except Exception as e:
        print(f"❌ Failed to save image: {e}")
        return None

def get_image(file_id):
    """Retrieve image from GridFS"""
    try:
        return fs.get(ObjectId(file_id))
    except:
        return None

def delete_image(file_id):
    """Delete image from GridFS"""
    try:
        fs.delete(ObjectId(file_id))
        return True
    except:
        return False

def save_lead(lead_data: Dict[str, Any]) -> int:
    """Save lead to MongoDB"""
    init_db()
    lead_id = get_next_id()
    
    # Save image if provided
    image_file_id = None
    if lead_data.get('image_url'):
        image_file_id = save_image(lead_data['image_url'], lead_id)
    
    lead_entry = {
        "id": lead_id,
        "name": lead_data.get("name", ""),
        "company": lead_data.get("company", ""),
        "email": lead_data.get("email", ""),
        "phone": lead_data.get("phone", ""),
        "requirement_type": lead_data.get("requirement_type", ""),
        "customer_type": lead_data.get("customer_type", ""),
        "other_customer_type": lead_data.get("other_customer_type", ""),
        "message": lead_data.get("message", ""),
        "source": lead_data.get("source", "web_form"),
        "image_file_id": image_file_id,
        "image_url": f"/api/images/{image_file_id}" if image_file_id else None,
        "status": "new",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    leads_collection.insert_one(lead_entry)
    print(f"✅ Lead saved with ID: {lead_id}")
    return lead_id

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
    query = {}
    
    if status:
        query["status"] = status
    if requirement_type:
        query["requirement_type"] = requirement_type
    if customer_type:
        query["customer_type"] = customer_type
    
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from.isoformat()
        if date_to:
            date_query["$lte"] = date_to.isoformat()
        if date_query:
            query["created_at"] = date_query
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    
    leads = list(leads_collection.find(query).skip(offset).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for lead in leads:
        lead["_id"] = str(lead["_id"])
    
    return leads

def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """Get single lead by ID"""
    lead = leads_collection.find_one({"id": lead_id})
    if lead:
        lead["_id"] = str(lead["_id"])
    return lead

def update_lead_status(lead_id: int, status: str) -> bool:
    """Update lead status"""
    result = leads_collection.update_one(
        {"id": lead_id},
        {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
    )
    return result.modified_count > 0

def get_leads_statistics() -> Dict:
    """Get statistics about leads"""
    total = leads_collection.count_documents({})
    
    stats = {
        "total_leads": total,
        "new_count": leads_collection.count_documents({"status": "new"}),
        "contacted_count": leads_collection.count_documents({"status": "contacted"}),
        "converted_count": leads_collection.count_documents({"status": "converted"}),
        "closed_count": leads_collection.count_documents({"status": "closed"}),
        "with_images": leads_collection.count_documents({"image_file_id": {"$ne": None}}),
        "requirement_counts": {},
        "customer_type_counts": {}
    }
    
    # Get counts by requirement type
    pipeline = [{"$group": {"_id": "$requirement_type", "count": {"$sum": 1}}}]
    for result in leads_collection.aggregate(pipeline):
        if result["_id"]:
            stats["requirement_counts"][result["_id"]] = result["count"]
    
    # Get counts by customer type
    pipeline = [{"$group": {"_id": "$customer_type", "count": {"$sum": 1}}}]
    for result in leads_collection.aggregate(pipeline):
        if result["_id"]:
            stats["customer_type_counts"][result["_id"]] = result["count"]
    
    # Today's leads
    today = datetime.now().date().isoformat()
    stats["today_leads"] = leads_collection.count_documents({
        "created_at": {"$regex": f"^{today}"}
    })
    
    return stats

def delete_lead(lead_id: int) -> bool:
    """Delete lead by ID"""
    # Get lead to delete image
    lead = leads_collection.find_one({"id": lead_id})
    if lead and lead.get('image_file_id'):
        delete_image(lead['image_file_id'])
        print(f"🗑️ Deleted image from MongoDB")
    
    result = leads_collection.delete_one({"id": lead_id})
    return result.deleted_count > 0

def export_leads() -> List[Dict]:
    """Export all leads"""
    leads = list(leads_collection.find({}))
    for lead in leads:
        lead["_id"] = str(lead["_id"])
    return leads