from django.urls import re_path
from .views import (CreateImage,
                    CreateImageEdit,
                    CreateImageVariation)

urlpatterns = [
    re_path('createImage/', CreateImage.as_view(), name='create-image'),
    re_path('createImageEdit/', CreateImageEdit.as_view(), name='edit-image-edit'),
    re_path('createImageVariation/', CreateImageVariation.as_view(), name='create-image-variation'),
]
