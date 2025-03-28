import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'investment_management_app.settings')
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from decimal import Decimal
import pandas as pd
import pytz
from datetime import datetime, timedelta

from .models import (
    Portfolio, Holding, Trade, ContactMessage,
    MockOrder, Stock, StockPrice, PortfolioPerformance, StockAlert
)
from .views import *
from .alpaca_api import get_stock_price, get_historical_data

# tests

class PortfolioMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.portfolio = Portfolio.objects.create(user=self.user, balance=10000.00)
        
        # Create sample trades
        Trade.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=10,
            trade_type='buy',
            trade_price=150.00
        )
        Trade.objects.create(
            portfolio=self.portfolio,
            symbol='MSFT',
            quantity=5,
            trade_type='buy',
            trade_price=200.00
        )

    def test_total_profit_loss_calculation(self):
        with patch.object(Holding, 'stock_price') as mock_stock_price:
            mock_stock_price.return_value = 160.00  # AAPL price
            Holding.objects.create(
                portfolio=self.portfolio,
                symbol='AAPL',
                quantity=10,
                average_price=150.00
            )
            # MSFT holding with different price
            Holding.objects.create(
                portfolio=self.portfolio,
                symbol='MSFT',
                quantity=5,
                average_price=200.00
            ).stock_price.return_value = 210.00
            
            expected_profit = (10*(160-150) + 5*(210-200))
            self.assertEqual(self.portfolio.total_profit_loss(), expected_profit)

    def test_gains_percentage_with_zero_invested(self):
        self.portfolio.trades.all().delete()
        self.assertEqual(self.portfolio.gains_percentage(), 0)

class MockOrderModelTests(TestCase):
    def test_mock_order_creation(self):
        user = User.objects.create_user(username='orderuser', password='orderpass')
        portfolio = Portfolio.objects.create(user=user, balance=5000.00)
        order = MockOrder.objects.create(
            user=user,
            portfolio=portfolio,
            symbol='TSLA',
            quantity=5,
            order_type='buy',
            price_at_execution=700.00,
            status='pending'
        )
        self.assertEqual(str(order), "orderuser BUY TSLA x5 at $700.0")

class AuthViewTests(TestCase):
    def test_registration_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'differentpassword'
        })
        self.assertContains(response, "The two password fields didn't match.")

    def test_login_success(self):
        User.objects.create_user(username='loginuser', password='loginpass')
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'loginpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

class PortfolioViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='portuser', password='portpass')
        self.client.login(username='portuser', password='portpass')
        self.portfolio = Portfolio.objects.create(user=self.user, name="Test", balance=1000.00)

    def test_create_portfolio_success(self):
        response = self.client.post(reverse('create_portfolio'), {
            'name': 'New Portfolio',
            'balance': '5000.00'
        })
        self.assertEqual(Portfolio.objects.count(), 2)
        self.assertRedirects(response, reverse('dashboard'))

    def test_delete_portfolio_post(self):
        response = self.client.post(reverse('delete_portfolio', args=[self.portfolio.id]))
        self.assertEqual(Portfolio.objects.count(), 0)
        self.assertRedirects(response, reverse('dashboard'))

class MockTradeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tradeuser', password='tradepass')
        self.client.login(username='tradeuser', password='tradepass')
        self.portfolio = Portfolio.objects.create(user=self.user, balance=10000.00)

    @patch('investment_manager_main.views.get_stock_price')
    def test_buy_trade_success(self, mock_price):
        mock_price.return_value = 150.00
        response = self.client.post(
            reverse('mock_trade', args=[self.portfolio.id]),
            {'trade_type': 'buy', 'symbol': 'AAPL', 'quantity': '10'}
        )
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.balance, Decimal('8500.00'))
        self.assertEqual(Holding.objects.count(), 1)

    @patch('investment_manager_main.views.get_stock_price')
    def test_sell_trade_insufficient_shares(self, mock_price):
        mock_price.return_value = 150.00
        Holding.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=5,
            average_price=140.00
        )
        response = self.client.post(
            reverse('mock_trade', args=[self.portfolio.id]),
            {'trade_type': 'sell', 'symbol': 'AAPL', 'quantity': '10'}
        )
        self.assertContains(response, "You do not have enough shares")

class AlpacaAPITests(TestCase):
    @patch('investment_manager_main.alpaca_api.REST')
    def test_get_stock_price_success(self, mock_rest):
        mock_instance = MagicMock()
        mock_instance.get_latest_trade.return_value = MagicMock(price=150.0)
        mock_rest.return_value = mock_instance

        price = get_stock_price('AAPL')
        self.assertEqual(price, 150.0)

    @patch('investment_manager_main.alpaca_api.REST')
    def test_get_historical_data_failure(self, mock_rest):
        mock_instance = MagicMock()
        mock_instance.get_bars.return_value = MagicMock(df=pd.DataFrame())
        mock_rest.return_value = mock_instance

        data = get_historical_data('INVALID', days=7)
        self.assertIsNone(data)

class URLResolutionTests(TestCase):
    def test_stock_history_url_resolves(self):
        match = resolve('/stock-history/AAPL/')
        self.assertEqual(match.func, stock_history_display)
        self.assertEqual(match.kwargs['symbol'], 'AAPL')

    def test_external_info_url_resolves(self):
        match = resolve('/external-information/')
        self.assertEqual(match.func, external_information)

class StockAlertModelTests(TestCase):
    def test_alert_creation(self):
        user = User.objects.create_user(username='alertuser', password='alertpass')
        alert = StockAlert.objects.create(
            user=user,
            symbol='GOOGL',
            target_price=2500.00
        )
        self.assertEqual(str(alert), "Alert for GOOGL at $2500.0")
        self.assertTrue(alert.is_active)
