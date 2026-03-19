import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def custom_serializer(obj):

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, (UUID, Decimal)):
        return str(obj)

    return str(obj)


def format_json(data):

    return json.dumps(
        data,
        default=custom_serializer,
        indent=2
    )