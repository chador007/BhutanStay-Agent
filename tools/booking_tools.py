import json
# You no longer need SQLAlchemy's text or engine here
from db.database import get_db_cursor 

def createBooking(
    guest_id: str, property_id: str, room_id: str,
    check_in_date, check_out_date, adults: int,
    children: int, payment_method: str, special_requests: str = None
):
    print("Tool createBooking called")

    try:
        query = """
        INSERT INTO bookings(
            guest_id, property_id, room_id, check_in_date, 
            check_out_date, adults, children, payment_method, booking_status
        )
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
        RETURNING id;
        """
        params = (guest_id, property_id, room_id, check_in_date, 
                  check_out_date, adults, children, payment_method)

        with get_db_cursor() as cur:
            cur.execute(query, params)
            booking_id = cur.fetchone()[0]
            # No need for manual commit; your @contextmanager handles it!
            return f"Booking created successfully. Booking ID: {booking_id}"

    except Exception as e:
        return f"Error creating booking: {str(e)}"

def cancelBooking(booking_id: str, reason: str):
    print("Tool cancelBooking called")

    try:
        query = """
        UPDATE bookings
        SET booking_status='cancelled',
            cancellation_reason=%s,
            cancelled_at=NOW()
        WHERE id=%s;
        """
        with get_db_cursor() as cur:
            cur.execute(query, (reason, booking_id))
            return "Booking cancelled successfully"

    except Exception as e:
        return f"Error cancelling booking: {str(e)}"

def getGuestBookings(guest_id: str):
    print("Tool getGuestBookings called")

    try:
        query = """
        SELECT 
            b.booking_code, b.check_in_date, b.check_out_date,
            b.booking_status, b.payment_status, b.grand_total,
            p.name AS property_name
        FROM bookings b
        JOIN properties p ON p.id=b.property_id
        WHERE b.guest_id=%s;
        """
        with get_db_cursor() as cur:
            cur.execute(query, (guest_id,))
            rows = cur.fetchall()
            
            # Get column names for dictionary mapping
            colnames = [desc[0] for desc in cur.description]
            data = [dict(zip(colnames, row)) for row in rows]

            return json.dumps(data, default=str) # default=str handles dates/decimals

    except Exception as e:
        return f"Error fetching bookings: {str(e)}"