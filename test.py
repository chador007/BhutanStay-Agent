import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import text

from database import get_db

def custom_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (UUID, Decimal)):
        return str(obj)
    return str(obj) # Fallback for anything else

  
print("Tool create_booking was called")
db_wrapper = get_db()
engine = db_wrapper._engine if hasattr(db_wrapper, "_engine") else db_wrapper
# Fixed: Added parentheses to .connect()
with engine.connect() as connection:
    query = text("SELECT id, booking_code FROM bookings ORDER BY created_at DESC LIMIT 1")
    result = connection.execute(query).fetchone()
    last_id = result[0]
    last_booking_code = result[1]
    print(last_id)
