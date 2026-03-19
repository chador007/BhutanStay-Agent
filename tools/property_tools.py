import json
from sqlalchemy import text
from db.database import get_db
from datetime import date
from .utils import custom_serializer

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