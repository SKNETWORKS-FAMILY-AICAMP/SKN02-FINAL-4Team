from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path("get-response/", views.chatbot_response, name="chatbot_response"),
    path('past-chats/', views.chat_list, name='chat_list'),  # List past chats
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),  # View specific chat
    path('new/', views.new_chat, name='new_chat'),
    path('delete-chat/<int:chat_id>/', views.delete_chat, name='delete_chat'),  # Soft delete a chat
]
