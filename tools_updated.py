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
    return str(obj) 


# READ TOOLS
def searchProperties(
    city: str = None,
    property_type: str = None,
    checkInDate: date = None,
    checkOutDate: date = None,
    adults: int = None,
    children: int = None,
    minPrice: float = None,
    maxPrice: float = None,
    amenities: list[str] = None,
    rating: float = None
) -> str:
    """
    Search properties and rooms based on filters.

    Parameters
    ----------
    city : filter properties by city
    property_type : hotel, resort, apartment etc.
    checkInDate : requested check-in date
    checkOutDate : requested check-out date
    adults : number of adults
    children : number of children
    minPrice : minimum room price
    maxPrice : maximum room price
    amenities : list of amenities like wifi, parking
    rating : minimum property rating
    """

    print("Tool searchProperties called")

    db_wrapper = get_db()
    engine = db_wrapper._engine if hasattr(db_wrapper, "_engine") else db_wrapper

    try:

        sql_parts = ["""
        SELECT 
            p.id AS property_id,
            p.name,
            p.description,
            p.address,
            p.city,
            p.rating,
            p.amenities,
            pt.name AS property_type,
            r.id AS room_id,
            r.room_number,
            r.capacity,
            r.base_price,
            rt.name AS room_type
        FROM properties p
        JOIN property_types pt ON p.property_type_id = pt.id
        LEFT JOIN rooms r ON r.property_id = p.id
        LEFT JOIN room_types rt ON r.room_type_id = rt.id
        WHERE p.status = 'approved'
        AND p.deleted_at IS NULL
        AND r.is_active = TRUE
        """]

        params = {}

        # City filter
        if city:
            sql_parts.append("AND p.city ILIKE :city")
            params["city"] = f"%{city}%"

        # Property type filter
        if property_type:
            sql_parts.append("AND pt.name ILIKE :property_type")
            params["property_type"] = f"%{property_type}%"

        # Rating filter
        if rating:
            sql_parts.append("AND p.rating >= :rating")
            params["rating"] = rating

        # Price filters
        if minPrice:
            sql_parts.append("AND r.base_price >= :minPrice")
            params["minPrice"] = minPrice

        if maxPrice:
            sql_parts.append("AND r.base_price <= :maxPrice")
            params["maxPrice"] = maxPrice

        # Capacity filter
        if adults or children:
            total_guests = (adults or 0) + (children or 0)
            sql_parts.append("AND r.capacity >= :capacity")
            params["capacity"] = total_guests

        # Amenities filter
        if amenities:
            for i, amenity in enumerate(amenities):
                key = f"amenity_{i}"
                sql_parts.append(f"AND p.amenities ILIKE :{key}")
                params[key] = f"%{amenity}%"

        # Availability check
        if checkInDate and checkOutDate:
            sql_parts.append("""
            AND r.id NOT IN (
                SELECT room_id FROM bookings
                WHERE booking_status NOT IN ('cancelled')
                AND (
                    check_in_date < :checkOutDate
                    AND check_out_date > :checkInDate
                )
            )
            """)
            params["checkInDate"] = checkInDate
            params["checkOutDate"] = checkOutDate

        final_query = text(" ".join(sql_parts))

        with engine.connect() as connection:
            result = connection.execute(final_query, params)
            rows = result.fetchall()

            if not rows:
                return "No properties found matching your search."

            data = [dict(zip(result.keys(), row)) for row in rows]

            return json.dumps(data, default=custom_serializer, indent=2)

    except Exception as e:
        return f"Database Error: {str(e)}"
    
def compareProperties(property_ids: list[str]) -> str:

    print("Tool compareProperties called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        SELECT 
            p.id,
            p.name,
            p.rating,
            p.reviews_count,
            p.amenities,
            pt.name AS property_type
        FROM properties p
        JOIN property_types pt ON pt.id=p.property_type_id
        WHERE p.id = ANY(:ids)
        """)

        with engine.connect() as conn:

            result = conn.execute(query, {"ids": property_ids})
            rows = result.fetchall()

            data = [dict(zip(result.keys(), row)) for row in rows]

            return json.dumps(data, default=custom_serializer, indent=2)

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
    
def getPropertyDetails(property_id: str):

    print("Tool getPropertyDetails called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        SELECT 
            p.name,
            p.description,
            p.address,
            p.city,
            p.country,
            p.rating,
            p.reviews_count,
            p.amenities,
            p.images,
            p.check_in_time,
            p.check_out_time,
            o.name AS owner_name,
            o.email,
            o.phone
        FROM properties p
        JOIN owners o ON o.id = p.owner_id
        WHERE p.id = :pid
        """)

        with engine.connect() as conn:

            result = conn.execute(query, {"pid": property_id})
            row = result.fetchone()

            if not row:
                return "Property not found"

            return json.dumps(dict(zip(result.keys(), row)))

    except Exception as e:
        return str(e)
    
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
    
def createBooking(
    guest_id: str,
    property_id: str,
    room_id: str,
    check_in_date,
    check_out_date,
    adults: int,
    children: int,
    payment_method: str,
    special_requests: str = None
):

    print("Tool createBooking called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        INSERT INTO bookings(
            guest_id,
            property_id,
            room_id,
            check_in_date,
            check_out_date,
            adults,
            children,
            payment_method,
            booking_status
        )
        VALUES(
            :guest,
            :property,
            :room,
            :checkin,
            :checkout,
            :adults,
            :children,
            :payment,
            'confirmed'
        )
        RETURNING id
        """)

        params = {
            "guest": guest_id,
            "property": property_id,
            "room": room_id,
            "checkin": check_in_date,
            "checkout": check_out_date,
            "adults": adults,
            "children": children,
            "payment": payment_method
        }

        with engine.connect() as conn:

            result = conn.execute(query, params)
            booking_id = result.fetchone()[0]
            conn.commit()

            return f"Booking created successfully. Booking ID: {booking_id}"

    except Exception as e:
        return str(e)
    
def cancelBooking(booking_id: str, reason: str):

    print("Tool cancelBooking called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        UPDATE bookings
        SET booking_status='cancelled',
        cancellation_reason=:reason,
        cancelled_at=NOW()
        WHERE id=:id
        """)

        with engine.connect() as conn:

            conn.execute(query, {"id": booking_id, "reason": reason})
            conn.commit()

            return "Booking cancelled successfully"

    except Exception as e:
        return str(e)
    
def getGuestBookings(guest_id: str):

    print("Tool getGuestBookings called")

    db = get_db()
    engine = db._engine if hasattr(db, "_engine") else db

    try:

        query = text("""
        SELECT 
            b.booking_code,
            b.check_in_date,
            b.check_out_date,
            b.booking_status,
            b.payment_status,
            b.grand_total,
            p.name AS property_name
        FROM bookings b
        JOIN properties p ON p.id=b.property_id
        WHERE b.guest_id=:gid
        """)

        with engine.connect() as conn:

            result = conn.execute(query, {"gid": guest_id})
            rows = result.fetchall()

            data = [dict(zip(result.keys(), row)) for row in rows]

            return json.dumps(data)

    except Exception as e:
        return str(e)
    