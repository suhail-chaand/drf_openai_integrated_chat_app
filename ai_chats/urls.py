from django.urls import re_path
from .views import (GetModelResponse,
                    CreateChatSession,
                    StreamModelResponse,
                    GetChatConversations)

urlpatterns = [
    re_path('createChatSession', CreateChatSession.as_view(), name='create-chat-session'),
    re_path('getChatConversations/(?P<pk>.+)', GetChatConversations.as_view(), name='get-chat-conversations'),
    re_path('getModelResponse/(?P<pk>.+)', GetModelResponse.as_view(), name='get-chat-model-response'),
    re_path('streamModelResponse/(?P<pk>.+)', StreamModelResponse.as_view(), name='stream-chat-model-response'),
]
