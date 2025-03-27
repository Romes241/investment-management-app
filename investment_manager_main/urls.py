from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    path('create-portfolio/', views.create_portfolio, name='create_portfolio'),
    path('portfolio/<int:portfolio_id>/', views.portfolio_details, name='portfolio_details'),  
    path('portfolio/<int:portfolio_id>/delete/', views.delete_portfolio, name='delete_portfolio'), 
    path('portfolio/<int:portfolio_id>/mock-trade/', views.mock_trade, name='mock_trade'),
    path('history/', views.stock_history, name='stock_history'),
    path("get-stock-price/", views.get_stock_price_view, name="get_stock_price"),
    path("api/holdings/", views.get_user_holding, name="get_user_holding"),
    path("get-stock-history/", views.get_stock_history, name="get_stock_history"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
]
