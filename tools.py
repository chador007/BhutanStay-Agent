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
@tool
def search_inventory(
    city: str = None,
    property_name: str = None,
    property_type: str = None,
    owner_name: str = None,
    min_rating: float = None,
    max_price: float = None,
    room_number: str = None,
) -> str:
    """
    Search for properties and rooms. 
    - Use 'query' for semantic 'vibe' searches (e.g., 'luxury views', 'traditional service').
    - Use 'city', 'property_type', and 'owner_name' for specific filters.
    - Use 'min_rating' and 'max_price' for quality and budget requirements.
    """
    print("Tool search_inventory was called")
    db_wrapper = get_db()
    engine = db_wrapper._engine if hasattr(db_wrapper, "_engine") else db_wrapper

    try:
        sql_parts = ["""
            SELECT 
                p.name, 
                p.description,
                p.address,
                p.city,
                p.rating,
                p.amenities,
                pt.name AS property_category,
                o.name AS owner_name,
                o.email AS owner_contact,
                r.room_number,
                r.base_price,
                rt.name AS room_style
            FROM properties p
            JOIN property_types pt ON p.property_type_id = pt.id
            JOIN owners o ON p.owner_id = o.id
            LEFT JOIN rooms r ON r.property_id = p.id
            LEFT JOIN room_types rt ON r.room_type_id = rt.id
            WHERE p.status = 'approved' AND p.deleted_at IS NULL
        """]
        params = {}

        if city:
            sql_parts.append("AND p.city ILIKE :city")
            params["city"] = city 
        if property_name:
            sql_parts.append("AND p.name ILIKE :property_name")
            params["property_name"] = property_name

        if property_type:
            sql_parts.append("AND pt.name ILIKE :property_type")
            params["property_type"] = property_type

        if owner_name:
            sql_parts.append("AND o.name ILIKE :owner_name")
            params["owner_name"] = owner_name

        if min_rating:
            sql_parts.append("AND p.rating >= :min_rating")
            params["min_rating"] = min_rating
        
        if max_price:
            sql_parts.append("AND r.base_price <= :max_price")
            params["max_price"] = max_price

        if room_number:
            sql_parts.append("AND r.room_number = :room_number")
            params["room_number"] = room_number
       
        final_query = text(" ".join(sql_parts))

        with engine.connect() as connection:
            result = connection.execute(final_query, params)
            rows = result.fetchall()
            print("Results after executing search inventory tool query:")
            for row in rows:
                print(row)
            
            if not rows:
                return "No properties found matching your search."

            data = [dict(zip(result.keys(), row)) for row in rows]
            return json.dumps(data, default=custom_serializer, indent=2)

    except Exception as e:
        return f"Database Error: {str(e)}"
    
@tool
def manage_reservations(
    booking_id: str = None,
    guest_name: str = None,
    start_date: str = None, 
    end_date: str = None,
    property_id: str = None,
    status: str = None
) -> str:
    """
    Search bookings OR find available rooms.
    - If start_date and end_date are provided, it returns rooms that are NOT booked.
    - Otherwise, it searches for existing reservation records.
    """
    print("Tool manage_reservations was called")
    db_wrapper = get_db()
    engine = db_wrapper._engine if hasattr(db_wrapper, "_engine") else db_wrapper

    try:
        if start_date and end_date:
            sql = text("""
                SELECT r.id, r.room_number, rt.name as type, p.name as hotel
                FROM rooms r
                JOIN room_types rt ON r.room_type_id = rt.id
                JOIN properties p ON r.property_id = p.id
                WHERE r.id NOT IN (
                    SELECT b.room_id 
                    FROM bookings b 
                    WHERE b.status != 'cancelled'
                    AND (b.check_in_date < :end_date AND b.check_out_date > :start_date)
                )
                AND (:property_id IS NULL OR r.property_id = :property_id)
            """)
            params = {"start_date": start_date, "end_date": end_date, "property_id": property_id}
            
        else:
            sql_parts = ["""
                SELECT 
                    b.id AS booking_code,
                    b.check_in_date,
                    b.check_out_date,
                    b.status AS booking_status,
                    b.total_price,
                    g.name AS guest_name,
                    g.email AS guest_email,
                    -- Use JSON aggregation to bundle rooms for this booking
                    json_agg(json_build_object(
                        'room_number', r.room_number,
                        'room_type', rt.name
                    )) AS booked_rooms
                FROM bookings b
                JOIN guests g ON b.guest_id = g.id
                LEFT JOIN rooms r ON b.id = r.booking_id
                LEFT JOIN room_types rt ON r.room_type_id = rt.id
                WHERE b.deleted_at IS NULL
            """]
            params = {}

            if booking_id:
                sql_parts.append("AND b.id = :booking_id")
                params["booking_id"] = booking_id

            if guest_name:
                sql_parts.append("AND g.name ILIKE :guest_name")
                params["guest_name"] = f"%{guest_name}%"

            if status:
                sql_parts.append("AND b.status = :status")
                params["status"] = status

            # Always group by the unique identifiers of the main record
            sql_parts.append("GROUP BY b.id, g.id")
            
            sql = text(" ".join(sql_parts))
            pass

        with engine.connect() as connection:
            result = connection.execute(sql, params)
            rows = result.fetchall()
            print("Results after executing manage reservation tool query:")
            for row in rows:
                print(row)
            return json.dumps([dict(row) for row in rows], default=str)

    except Exception as e:
        return f"Database Error: {str(e)}"
    
# WRITE TOOLS
@tool
def create_booking(
    property_name:str,
    room_number:str,
    check_in_date: date,
    check_out_date: date,
    number_of_adults: int = 1,
    number_of_children: int = 0,
    special_request:list[str] = None

)-> str:
    
    """
    Create bookings based on the details given by the user.
    """
    print("Tool create_booking was called")
    db_wrapper = get_db()
    engine = db_wrapper._engine if hasattr(db_wrapper, "_engine") else db_wrapper
    try:
        with engine.connect() as connection:
            
            # fetch the last booking code and id
            query = text("SELECT id, booking_code FROM bookings ORDER BY created_at DESC LIMIT 1")
            result = connection.execute(query).fetchone()
            last_id = result[0]
            last_booking_code = result[1]

            query = text("SELECT id, booking_code FROM bookings ORDER BY created_at DESC LIMIT 1")
            result = connection.execute(query).fetchone()
            last_id = result[0]
            last_booking_code = result[1]

            query = text("SELECT * FROM properties WHERE name = :property_name")
            result = connection.execute(query, {"property_name": property_name})
            data = [dict(zip(result.keys(), row)) for row in result.fetchall()]
            property_id = data[0]["id"]

            query = text("SELECT * FROM room WHERE room_number = :room_number")
            result = connection.execute(query, {"room_number": room_number})
            data = [dict(zip(result.keys(), row)) for row in result.fetchall()]
            room_id = data[0]["id"]
            price = data[0]["base_price"]

            guest_id = "90000001-0000-0000-0000-000000000001"
            query = text("INSERT INTO bookings (id, booking_code, guest_id, property_id, room_id, check_in_date, check_out_date, nights, adults, children, room_rate, subtotal, tax_amount, discount_amount, grand_total, payment_status, payment_method, booking_status, special_requests, cancellation_reason, cancelled_at) VALUES (:id, :booking_code, :guest_id, :property_id, :room_id, :check_in_date, :check_out_date, :nights, :adults, :children, :rate, :subtotal, :tax, :discount, :total, :pay_status, :pay_method, :status, :req, :reason, :cancelled_at);")


    except Exception as e:
        return f"Database Error: {str(e)}"
    
    print(create_booking.invoke(""))