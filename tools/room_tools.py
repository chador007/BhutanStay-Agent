import json
from sqlalchemy import text
from db.database import get_db
from .utils import custom_serializer

def getRoomDetails(room_id: str):

    print("Tool getRoomDetails called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        SELECT 
            r.room_number,
            r.floor,
            r.capacity,
            r.base_price,
            r.description,
            r.amenities,
            rt.name AS room_type
        FROM rooms r
        JOIN room_types rt ON rt.id = r.room_type_id
        WHERE r.id = :rid
        """)

        with engine.connect() as conn:

            result = conn.execute(query, {"rid": room_id})
            row = result.fetchone()

            if not row:
                return "Room not found"

            return json.dumps(dict(zip(result.keys(), row)))

    except Exception as e:
        return str(e)
    

def checkRoomAvailability(
    property_id: str,
    checkInDate,
    checkOutDate,
    adults: int = None,
    children: int = None
):

    print("Tool checkRoomAvailability called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    capacity = (adults or 0) + (children or 0)

    try:

        query = text("""
        SELECT r.id, r.room_number, r.capacity, r.base_price
        FROM rooms r
        WHERE r.property_id = :property_id
        AND r.capacity >= :capacity
        AND r.id NOT IN (
            SELECT room_id FROM bookings
            WHERE booking_status != 'cancelled'
            AND check_in_date < :checkout
            AND check_out_date > :checkin
        )
        """)

        params = {
            "property_id": property_id,
            "capacity": capacity,
            "checkin": checkInDate,
            "checkout": checkOutDate
        }

        with engine.connect() as conn:

            result = conn.execute(query, params)
            rows = result.fetchall()

            data = [dict(zip(result.keys(), row)) for row in rows]

            return json.dumps(data, default=custom_serializer)

    except Exception as e:
        return str(e)
