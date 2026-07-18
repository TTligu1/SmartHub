from django.contrib import admin
from .models import UserProfile, ChatSession, ChatMessage

# Modellarni admin panelga qo'shish
admin.site.register(UserProfile)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)