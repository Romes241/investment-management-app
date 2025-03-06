from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('dashboard/', views.dashboard, name='dashboard'),  
    path('register/', views.register, name='register'),
    path('history/', views.stock_history, name='stock_history'),
    path('mock-trade/', views.mock_trade, name='mock_trade'),
]
