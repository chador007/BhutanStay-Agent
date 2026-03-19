import json
from sqlalchemy import text
from db.database import get_db

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