from rest_framework.utils import json
from rest_framework.renderers import BaseRenderer


class CustomResponseRenderer(BaseRenderer):
    format = 'txt'
    media_type = 'application/json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = {
            'status_code': renderer_context['response'].status_code,
            'data': data.get('data') if data.get('data') else None,
            'error': data.get('error') if data.get('error') else None,
            'message': "FAILURE" if data.get('error') else "SUCCESS",
        }

        return json.dumps(response)
