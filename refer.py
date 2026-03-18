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