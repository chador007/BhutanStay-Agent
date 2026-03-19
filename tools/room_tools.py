import json
from db.database import get_db_cursor 
from .utils import custom_serializer

def getRoomDetails(room_id: str):
    print("Tool getRoomDetails called")

    try:
        query = """
        SELECT 
            r.room_number, r.floor, r.capacity, r.base_price,
            r.description, r.amenities, rt.name AS room_type
        FROM rooms r
        JOIN room_types rt ON rt.id = r.room_type_id
        WHERE r.id = %s;
        """
        with get_db_cursor() as cur:
            cur.execute(query, (room_id,))
            row = cur.fetchone()

            if not row:
                return "Room not found"

            # Fetch column names for dictionary mapping
            colnames = [desc[0] for desc in cur.description]
            return json.dumps(dict(zip(colnames, row)), default=custom_serializer)

    except Exception as e:
        return f"Error fetching room details: {str(e)}"
    

def checkRoomAvailability(
    property_id: str,
    checkInDate,
    checkOutDate,
    adults: int = None,
    children: int = None
):
    print("Tool checkRoomAvailability called")

    # Calculate total capacity needed
    capacity = (adults or 0) + (children or 0)

    try:
        query = """
        SELECT r.id, r.room_number, r.capacity, r.base_price
        FROM rooms r
        WHERE r.property_id = %s
        AND r.capacity >= %s
        AND r.id NOT IN (
            SELECT room_id FROM bookings
            WHERE booking_status != 'cancelled'
            AND check_in_date < %s
            AND check_out_date > %s
        );
        """
        # Parameters must be in the exact order of the %s in the query
        params = (property_id, capacity, checkOutDate, checkInDate)

        with get_db_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

            colnames = [desc[0] for desc in cur.description]
            data = [dict(zip(colnames, row)) for row in rows]

            return json.dumps(data, default=custom_serializer)

    except Exception as e:
        return f"Error checking availability: {str(e)}"