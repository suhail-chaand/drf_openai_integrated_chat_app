from django.urls import re_path
from .views import (ModelsList,
                    FineTunesList)

urlpatterns = [
    re_path('models', ModelsList.as_view(), name='get-models-list'),
    re_path('fineTunes', FineTunesList.as_view(), name='get-fine-tunes-list'),
]
