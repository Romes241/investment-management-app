from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('dashboard/', views.dashboard, name='dashboard'),  
    path('register/', views.register, name='register'),
    path('history/', views.stock_history, name='stock_history'),
    path('mock-trade/', views.mock_trade, name='mock_trade'),

    #Potential Site URLs matching design spec
    #path('signup/', views.signup, name='Sign_Up'),
    #path('login/', views.login, name='Login'),
    #path('dashboard/', views.dashboard, name='Dashboard'),
    #path('portfolio/', views.portfolio, name='Portfolio'),
    #path('<id>/', views., name='Portfolio_Details'),
    #path('trade/', views.trade, name='Mock_Trade'),
    #path('analytics/', views.analytics, name='Analytics'),
    #path('about/', views.about, name='About'),
    #path('contact/', views.contact, name='Contact_Us'),
]
