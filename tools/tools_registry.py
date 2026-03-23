from .booking_tools import (
    createBooking,
    cancelBooking,
    getGuestBookings
)
from .property_tools import (
    searchProperties,
    compareProperties,
    getPropertyDetails
)
from .room_tools import (
    checkRoomAvailability,
    getRoomDetails
)

tools_map = {
    "searchProperties": searchProperties,
    "compareProperties": compareProperties,
    "checkRoomAvailability": checkRoomAvailability,
    "getPropertyDetails": getPropertyDetails,
    "getRoomDetails": getRoomDetails,
    "createBooking": createBooking,
    "cancelBooking": cancelBooking,
    "getGuestBookings": getGuestBookings
}


# TOOL_DESCRIPTIONS = [

# {
# "name": "searchProperties",
# "description": "Search for hotels based on location, price, rating and guest count",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "city": {"type": "string"},
#         "property_type": {"type": "string"},
#         "minPrice": {"type": "number"},
#         "maxPrice": {"type": "number"},
#         "adults": {"type": "integer"},
#         "children": {"type": "integer"},
#         "rating": {"type": "number"}
#     },
#     "required": ["city"]
# }
# },

# {
# "name": "checkRoomAvailability",
# "description": "Check if rooms are available for given dates",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "property_id": {"type": "string"},
#         "checkInDate": {"type": "string", "format": "date"},
#         "checkOutDate": {"type": "string", "format": "date"},
#         "adults": {"type": "integer"},
#         "children": {"type": "integer"}
#     },
#     "required": ["property_id", "checkInDate", "checkOutDate"]
# }
# },

# {
# "name": "getPropertyDetails",
# "description": "Get details about a specific hotel",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "property_id": {"type": "string"}
#     },
#     "required": ["property_id"]
# }
# },

# {
# "name": "getRoomDetails",
# "description": "Get information about a room",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "room_id": {"type": "string"}
#     },
#     "required": ["room_id"]
#     }
# },

# # {
# # "name": "createBooking",
# # "description": "Create a booking for a room",
# # "parameters": {
# #     "type": "object",
# #     "properties": {
# #         "property_id": {"type": "string"},
# #         "room_id": {"type": "string"},
# #         "check_in_date": {"type": "string", "format": "date"},
# #         "check_out_date": {"type": "string", "format": "date"},
# #         "adults": {"type": "integer"},
# #         "children": {"type": "integer"},
# #         "payment_method": {"type": "string"}
# #     },
# #     "required": [
# #         "property_id", 
# #         "room_id", 
# #         "check_in_date", 
# #         "check_out_date",
# #         "adults",
# #         "children",
# #         "payment_method"
# #     ]
# # }
# # },

# {
#   "name": "createBooking",
#   "description": "Generates a formatted booking confirmation message for the user to copy and paste into WhatsApp.",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "guest_name": {
#         "type": "string",
#         "description": "The name of the guest (e.g., Chador)"
#       },
#       "hotel_name": {
#         "type": "string", 
#         "description": "The name of the hotel (e.g., Wangchuk Hotel)"
#       },
#       "room_number": {
#         "type": "string",
#         "description": "The room number (e.g., 101)"
#       },
#       "room_price": {
#         "type": "string",
#         "description": "The price of the room including currency"
#       },
#       "check_in_date": {"type": "string", "format": "date"},
#       "check_out_date": {"type": "string", "format": "date"},
#       "adults": {"type": "integer"},
#       "children": {"type": "integer"}
#     },
#     "required": [
#       "guest_name",
#       "hotel_name",
#       "room_number",
#       "room_price",
#       "check_in_date",
#       "check_out_date",
#       "adults"
#     ]
#   }
# },

# {
# "name": "cancelBooking",
# "description": "Cancel a booking",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "booking_id": {"type": "string"},
#         "reason": {"type": "string"}
#     },
#     "required": ["booking_id"]
# }
# },

# {
# "name": "getGuestBookings",
# "description": "Get all bookings for a guest",
# "parameters": {
#     "type": "object",
#     "properties": {
#         "guest_id": {"type": "string"}
#     },
#     "required": ["guest_id"]
# }
# }

# ]

TOOL_DESCRIPTIONS = [
    {
        "type": "function",
        "function": {
            "name": "searchProperties",
            "description": "Search for hotels based on location, price, rating and guest count",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "property_type": {"type": "string"},
                    "minPrice": {"type": "number"},
                    "maxPrice": {"type": "number"},
                    "adults": {"type": "integer"},
                    "children": {"type": "integer"},
                    "rating": {"type": "number"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkRoomAvailability",
            "description": "Check if rooms are available for given dates",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {"type": "string"},
                    "checkInDate": {"type": "string", "format": "date"},
                    "checkOutDate": {"type": "string", "format": "date"},
                    "adults": {"type": "integer"},
                    "children": {"type": "integer"}
                },
                "required": ["property_id", "checkInDate", "checkOutDate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getPropertyDetails",
            "description": "Get details about a specific hotel",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {"type": "string"}
                },
                "required": ["property_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getRoomDetails",
            "description": "Get information about a room",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "string"}
                },
                "required": ["room_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "createBooking",
            "description": "Generates a formatted booking confirmation message for the user to copy and paste into WhatsApp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {"type": "string", "description": "The name of the guest (e.g., Chador)"},
                    "hotel_name": {"type": "string", "description": "The name of the hotel (e.g., Wangchuk Hotel)"},
                    "room_number": {"type": "string", "description": "The room number (e.g., 101)"},
                    "room_price": {"type": "string", "description": "The price of the room including currency"},
                    "check_in_date": {"type": "string", "format": "date"},
                    "check_out_date": {"type": "string", "format": "date"},
                    "adults": {"type": "integer"},
                    "children": {"type": "integer"}
                },
                "required": ["guest_name", "hotel_name", "room_number", "room_price", "check_in_date", "check_out_date", "adults"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancelBooking",
            "description": "Cancel a booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getGuestBookings",
            "description": "Get all bookings for a guest",
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_id": {"type": "string"}
                },
                "required": ["guest_id"]
            }
        }
    }
]