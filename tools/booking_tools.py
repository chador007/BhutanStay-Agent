import json
# You no longer need SQLAlchemy's text or engine here
from db.database import get_db_cursor 

# def createBooking(
#     property_id: str, 
#     room_id: str,
#     check_in_date: str, 
#     check_out_date: str, 
#     adults: int = 1,          
#     children: int = 0,         
#     payment_method: str = "Unspecified", 
#     special_requests: str = None
# ):  
#     print("Tool createBooking called")

#     try:
#         query = """
#         INSERT INTO bookings(
#             guest_id, property_id, room_id, check_in_date, 
#             check_out_date, adults, children, payment_method, booking_status
#         )
#         VALUES(%s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
#         RETURNING id;
#         """
#         params = (property_id, room_id, check_in_date, 
#                   check_out_date, adults, children, payment_method)

#         with get_db_cursor() as cur:
#             cur.execute(query, params)
#             booking_id = cur.fetchone()[0]
#             # No need for manual commit; your @contextmanager handles it!
#             return f"Booking created successfully. Booking ID: {booking_id}"

#     except Exception as e:
#         return f"Error creating booking: {str(e)}"
    

def createBooking(
    guest_name: str,
    hotel_name: str,
    room_number: str,
    room_price: str,
    check_in_date: str,
    check_out_date: str,
    adults: int,
    children: int = 0
):
    # This generates the exact format you requested for WhatsApp
    whatsapp_template = (
        f"Name: {guest_name}\n"
        f"Hotel Name: {hotel_name}\n"
        f"Room Number: {room_number}\n"
        f"Room Price: {room_price}\n\n"
        f"Stay Dates: {check_in_date} to {check_out_date}\n"
        f"Guests: {adults} Adults, {children} Children"
        f"\n\nYou can book this room by sending this message to our WhatsApp number: +1234567890"
    )
    
    return whatsapp_template



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