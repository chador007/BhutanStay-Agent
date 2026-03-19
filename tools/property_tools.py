import json
from db.database import get_db_cursor 
from .utils import custom_serializer

def searchProperties(
    city: str = None, property_type: str = None, checkInDate: str = None,
    checkOutDate: str = None, adults: int = None, children: int = None,
    minPrice: float = None, maxPrice: float = None,
    amenities: list[str] = None, rating: float = None
) -> str:
    print("Tool searchProperties called")

    try:
        # 1. Base Query
        sql = """
        SELECT 
            p.id AS property_id, p.name, p.description, p.address, p.city,
            p.rating, p.amenities, pt.name AS property_type, r.id AS room_id,
            r.room_number, r.capacity, r.base_price, rt.name AS room_type
        FROM properties p
        JOIN property_types pt ON p.property_type_id = pt.id
        LEFT JOIN rooms r ON r.property_id = p.id
        LEFT JOIN room_types rt ON r.room_type_id = rt.id
        WHERE p.status = 'approved' AND p.deleted_at IS NULL AND r.is_active = TRUE
        """
        
        params = []

        # 2. Dynamic Filtering
        if city:
            sql += " AND p.city ILIKE %s"
            params.append(f"%{city}%")
        if property_type:
            sql += " AND pt.name ILIKE %s"
            params.append(f"%{property_type}%")
        if rating:
            sql += " AND p.rating >= %s"
            params.append(rating)
        if minPrice:
            sql += " AND r.base_price >= %s"
            params.append(minPrice)
        if maxPrice:
            sql += " AND r.base_price <= %s"
            params.append(maxPrice)
        if adults or children:
            sql += " AND r.capacity >= %s"
            params.append((adults or 0) + (children or 0))
        
        if amenities:
            for amenity in amenities:
                sql += " AND p.amenities ILIKE %s"
                params.append(f"%{amenity}%")

        if checkInDate and checkOutDate:
            sql += """
            AND r.id NOT IN (
                SELECT room_id FROM bookings
                WHERE booking_status != 'cancelled'
                AND (check_in_date < %s AND check_out_date > %s)
            )
            """
            params.extend([checkOutDate, checkInDate])

        # 3. Execution
        with get_db_cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows:
                return "No properties found matching your search."

            colnames = [desc[0] for desc in cur.description]
            data = [dict(zip(colnames, row)) for row in rows]
            return json.dumps(data, default=custom_serializer, indent=2)

    except Exception as e:
        return f"Database Error: {str(e)}"

def compareProperties(property_ids: list[str]) -> str:
    print("Tool compareProperties called")
    try:
        # Psycopg2 handles 'ANY' with a tuple/list passed as a single %s
        query = """
        SELECT p.id, p.name, p.rating, p.reviews_count, p.amenities, pt.name AS property_type
        FROM properties p
        JOIN property_types pt ON pt.id=p.property_type_id
        WHERE p.id = ANY(%s);
        """
        with get_db_cursor() as cur:
            cur.execute(query, (property_ids,))
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            data = [dict(zip(colnames, row)) for row in rows]
            return json.dumps(data, default=custom_serializer, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def getPropertyDetails(property_id: str):
    print("Tool getPropertyDetails called")
    try:
        query = """
        SELECT p.name, p.description, p.address, p.city, p.country, p.rating,
               p.reviews_count, p.amenities, p.images, p.check_in_time,
               p.check_out_time, o.name AS owner_name, o.email, o.phone
        FROM properties p
        JOIN owners o ON o.id = p.owner_id
        WHERE p.id = %s;
        """
        with get_db_cursor() as cur:
            cur.execute(query, (property_id,))
            row = cur.fetchone()
            if not row:
                return "Property not found"
            colnames = [desc[0] for desc in cur.description]
            return json.dumps(dict(zip(colnames, row)), default=custom_serializer)
    except Exception as e:
        return f"Error: {str(e)}"