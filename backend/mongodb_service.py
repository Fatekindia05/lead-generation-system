import os
import base64
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
import gridfs
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from PIL import Image
import ssl
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://fatek_user:Fatek2026@cluster0.d5wpzja.mongodb.net/fatek_leads?appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "fatek_leads")

# Global variables for lazy connection
_client = None
_db = None
_leads_collection = None
_fs = None
_connection_error = None

def get_client():
    """Get MongoDB client - connects lazily"""
    global _client, _connection_error
    
    if _client is None and _connection_error is None:
        try:
            logger.info("🔌 Connecting to MongoDB...")
            
            # Try different connection approaches
            connection_attempts = [
                # Approach 1: Full SSL with ServerApi
                lambda: MongoClient(
                    MONGODB_URI,
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsAllowInvalidCertificates=False,
                    tlsAllowInvalidHostnames=False,
                    retryWrites=True,
                    w='majority',
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                ),
                # Approach 2: SSL with relaxed settings
                lambda: MongoClient(
                    MONGODB_URI,
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    tlsAllowInvalidHostnames=True,
                    retryWrites=True,
                    w='majority',
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                ),
                # Approach 3: No SSL (fallback)
                lambda: MongoClient(
                    MONGODB_URI,
                    server_api=ServerApi('1'),
                    tls=False,
                    retryWrites=True,
                    w='majority',
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                ),
            ]
            
            for attempt, create_client in enumerate(connection_attempts, 1):
                try:
                    logger.info(f"🔄 Connection attempt {attempt}...")
                    _client = create_client()
                    # Test connection
                    _client.admin.command('ping')
                    logger.info(f"✅ MongoDB connection successful! (attempt {attempt})")
                    _connection_error = None
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Attempt {attempt} failed: {e}")
                    _client = None
                    _connection_error = str(e)
            
            if _client is None:
                logger.error(f"❌ All connection attempts failed. Last error: {_connection_error}")
                
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            _connection_error = str(e)
            _client = None
    
    return _client

def get_db():
    """Get database instance"""
    global _db
    if _db is None:
        client = get_client()
        if client:
            _db = client[DB_NAME]
            logger.info(f"✅ Database '{DB_NAME}' selected")
        else:
            logger.warning("⚠️ No client available for database selection")
    return _db

def get_leads_collection():
    """Get leads collection"""
    global _leads_collection
    if _leads_collection is None:
        db = get_db()
        if db:
            _leads_collection = db["leads"]
            logger.info("✅ Leads collection selected")
        else:
            logger.warning("⚠️ No database available for collection selection")
    return _leads_collection

def get_fs():
    """Get GridFS instance"""
    global _fs
    if _fs is None:
        db = get_db()
        if db:
            _fs = gridfs.GridFS(db)
            logger.info("✅ GridFS initialized")
    return _fs

def check_connection():
    """Check if MongoDB is connected"""
    client = get_client()
    if client:
        try:
            client.admin.command('ping')
            return True
        except:
            return False
    return False

def init_db():
    """Initialize database collections and indexes"""
    try:
        db = get_db()
        if db is None:
            logger.warning("⚠️ Database not available, skipping init")
            return False
        
        # Create counters collection for auto-increment
        if db.counters.count_documents({"_id": "lead_id"}) == 0:
            db.counters.insert_one({"_id": "lead_id", "seq": 0})
        logger.info("✅ Database initialized")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Database init warning: {e}")
        return False

def get_next_id():
    """Get next auto-increment ID"""
    try:
        db = get_db()
        if db is None:
            logger.warning("⚠️ No database for ID generation")
            return 1
        counter = db.counters.find_one_and_update(
            {"_id": "lead_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return counter["seq"]
    except Exception as e:
        logger.warning(f"⚠️ Failed to get next ID: {e}")
        return 1

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
        
        fs = get_fs()
        if fs is None:
            logger.error("❌ GridFS not available")
            return None
        
        # Store in GridFS
        file_id = fs.put(
            image_data,
            filename=filename,
            metadata={
                "lead_id": lead_id,
                "uploaded_at": datetime.now()
            }
        )
        logger.info(f"✅ Image saved to MongoDB with ID: {file_id}")
        return str(file_id)
    except Exception as e:
        logger.error(f"❌ Failed to save image: {e}")
        return None

def get_image(file_id):
    """Retrieve image from GridFS"""
    try:
        fs = get_fs()
        if fs is None:
            return None
        return fs.get(ObjectId(file_id))
    except Exception as e:
        logger.error(f"❌ Failed to get image: {e}")
        return None

def delete_image(file_id):
    """Delete image from GridFS"""
    try:
        fs = get_fs()
        if fs is None:
            return False
        fs.delete(ObjectId(file_id))
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete image: {e}")
        return False

def save_lead(lead_data: Dict[str, Any]) -> int:
    """Save lead to MongoDB"""
    try:
        logger.info("📝 Saving lead to MongoDB...")
        
        # Check connection first
        if not check_connection():
            logger.warning("⚠️ MongoDB not connected, attempting to reconnect...")
            global _client
            _client = None
            get_client()
            if not check_connection():
                logger.error("❌ Cannot save lead: MongoDB connection failed")
                return 0
        
        # Initialize DB
        init_db()
        
        leads_collection = get_leads_collection()
        if leads_collection is None:
            logger.error("❌ Leads collection not available")
            return 0
        
        lead_id = get_next_id()
        logger.info(f"📝 Generated lead ID: {lead_id}")
        
        # Save image if provided
        image_file_id = None
        if lead_data.get('image_url'):
            logger.info("📸 Saving image...")
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
        logger.info(f"✅ Lead saved with ID: {lead_id}")
        return lead_id
    except Exception as e:
        logger.error(f"❌ Failed to save lead: {e}")
        return 0

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
    
    try:
        logger.info("🔍 Fetching leads from MongoDB...")
        
        # Check connection
        if not check_connection():
            logger.warning("⚠️ MongoDB not connected, attempting to reconnect...")
            global _client
            _client = None
            get_client()
            if not check_connection():
                logger.error("❌ Cannot fetch leads: MongoDB connection failed")
                return []
        
        leads_collection = get_leads_collection()
        if leads_collection is None:
            logger.error("❌ Leads collection not available")
            return []
        
        leads = list(leads_collection.find(query).skip(offset).limit(limit))
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        
        logger.info(f"✅ Retrieved {len(leads)} leads")
        return leads
    except Exception as e:
        logger.error(f"❌ Failed to get leads: {e}")
        return []

def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """Get single lead by ID"""
    try:
        leads_collection = get_leads_collection()
        if leads_collection is None:
            return None
        lead = leads_collection.find_one({"id": lead_id})
        if lead:
            lead["_id"] = str(lead["_id"])
        return lead
    except Exception as e:
        logger.error(f"❌ Failed to get lead: {e}")
        return None

def update_lead_status(lead_id: int, status: str) -> bool:
    """Update lead status"""
    try:
        leads_collection = get_leads_collection()
        if leads_collection is None:
            return False
        result = leads_collection.update_one(
            {"id": lead_id},
            {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"❌ Failed to update lead: {e}")
        return False

def get_leads_statistics() -> Dict:
    """Get statistics about leads"""
    stats = {
        "total_leads": 0,
        "new_count": 0,
        "contacted_count": 0,
        "converted_count": 0,
        "closed_count": 0,
        "with_images": 0,
        "today_leads": 0,
        "requirement_counts": {},
        "customer_type_counts": {}
    }
    
    try:
        logger.info("📊 Fetching statistics...")
        
        # Check connection
        if not check_connection():
            logger.warning("⚠️ MongoDB not connected for stats, returning zeros")
            return stats
        
        leads_collection = get_leads_collection()
        if leads_collection is None:
            logger.warning("⚠️ Leads collection not available for stats")
            return stats
        
        stats["total_leads"] = leads_collection.count_documents({})
        stats["new_count"] = leads_collection.count_documents({"status": "new"})
        stats["contacted_count"] = leads_collection.count_documents({"status": "contacted"})
        stats["converted_count"] = leads_collection.count_documents({"status": "converted"})
        stats["closed_count"] = leads_collection.count_documents({"status": "closed"})
        stats["with_images"] = leads_collection.count_documents({"image_file_id": {"$ne": None}})
        
        # Today's leads
        today = datetime.now().date().isoformat()
        stats["today_leads"] = leads_collection.count_documents({
            "created_at": {"$regex": f"^{today}"}
        })
        
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
        
        logger.info(f"✅ Statistics: {stats['total_leads']} total leads")
                
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
    
    return stats

def delete_lead(lead_id: int) -> bool:
    """Delete lead by ID"""
    try:
        leads_collection = get_leads_collection()
        if leads_collection is None:
            return False
        
        # Get lead to delete image
        lead = leads_collection.find_one({"id": lead_id})
        if lead and lead.get('image_file_id'):
            delete_image(lead['image_file_id'])
            logger.info(f"🗑️ Deleted image from MongoDB")
        
        result = leads_collection.delete_one({"id": lead_id})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"❌ Failed to delete lead: {e}")
        return False

def export_leads() -> List[Dict]:
    """Export all leads"""
    try:
        leads_collection = get_leads_collection()
        if leads_collection is None:
            return []
        leads = list(leads_collection.find({}))
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        return leads
    except Exception as e:
        logger.error(f"❌ Failed to export leads: {e}")
        return []