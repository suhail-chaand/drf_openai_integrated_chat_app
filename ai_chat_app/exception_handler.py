import json
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        response.data["error"] = json.dumps(response.data)

    return response
