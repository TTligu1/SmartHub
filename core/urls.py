from django.urls import path
from . import views

urlpatterns = [
    # Asosiy va asboblar sahifalari
    path('', views.home, name='home'),
    path('accounts/register/', views.register_view, name='register'),
    path('tools/', views.tools_home, name='tools_home'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),

    # Mini asboblar (Generators & Tools)
    path('qr-generator/', views.qr_generator, name='qr_generator'),
    path('barcode-generator/', views.barcode_generator, name='barcode_generator'),
    path('pdf-tools/', views.pdf_tools, name='pdf_tools'),
    path('image-tools/', views.image_tools, name='image_tools'),

    # Klaviatura poygasi (Typing Race) qismi
    path('race-arena/', views.race_arena, name='race_arena'),
    path('races-list/', views.races_list, name='races_list'),
    path('api/save-race/', views.save_race_result, name='save_race_result'),
    path('save-race-result/', views.save_race_result, name='save_race_result'),

    # Tizim foydalanuvchilari va Chat yo'llari
    path('system-users/', views.user_activity_list, name='user_activity_list'),
    path('chat/', views.user_chat_room, name='user_chat_room'),

    # 📍 QO'SHILDI: Telegram Chat tizimi uchun API yo'nalishlari
    path('api/chat-users/', views.get_chat_users, name='get_chat_users'),
    path('api/get-messages/', views.get_messages, name='get_messages'),
    path('api/send-message/', views.send_message, name='send_message'),

    # 💡 QO'SHILDI: Shablonlarda eski qolib ketgan tools_list bo'lsa xato bermasligi uchun dublyaj yo'nalish
    path('tools/list/', views.tools_home, name='tools_list'),
]