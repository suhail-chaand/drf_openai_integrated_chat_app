from django.db import models
from django.utils import timezone


class Chat(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)


class Conversation(models.Model):
    ROLE_CHOICES = (
        ('user', 'user'),
        ('system', 'system'),
        ('assistant', 'assistant')
    )
    chat = models.ForeignKey(Chat, null=False, blank=False, on_delete=models.CASCADE)
    role = models.TextField(null=False, blank=False, default="user", choices=ROLE_CHOICES)
    content = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)
