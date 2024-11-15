from django.contrib import admin
from django.urls import path, include
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')), 
    path('common/', include('common.urls')),
    path("chatbot/", include("chatbot.urls")),
]
