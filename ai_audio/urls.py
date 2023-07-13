from django.urls import re_path
from .views import (Translate,
                    Transcribe)

urlpatterns = [
    re_path('transcribe', Transcribe.as_view(), name='transcribe'),
    re_path('translate', Translate.as_view(), name='translate'),
]
