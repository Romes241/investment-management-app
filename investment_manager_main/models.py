from django.db import models
from django.contrib.auth.models import User
from .alpaca_api import get_stock_price

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios")
    name = models.CharField(max_length=100, default="Default Portfolio")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_invested(self):
        trades = self.trades.all()
        if not trades.exists():  
            return 0.0
        return sum(trade.trade_price * trade.quantity for trade in trades)

    def total_profit_loss(self):
        trades = self.trades.all()
        if not trades.exists():
            return 0.0
        return sum(((trade.price_ceiling or trade.trade_price) - trade.trade_price) * trade.quantity for trade in trades)
    
    def gains_percentage(self):
        invested = self.total_invested()
        if invested == 0:
            return 0
        return round((self.total_profit_loss() / invested) * 100, 2)
    
    def total_value(self):
        holdings = self.holdings.all()
        holdings_value = sum(h.stock_price() * h.quantity for h in holdings)
        return holdings_value + float(self.balance)  
    
    def __str__(self):
        return f"{self.user.username} - {self.name} (£{self.balance})"


class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, related_name="holdings", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    average_price = models.FloatField()

    def stock_price(self):
        return get_stock_price(self.symbol)

    def current_value(self):
        return self.stock_price() * self.quantity

    def __str__(self):
        return f"{self.symbol} - {self.quantity} shares in {self.portfolio.name}"


class Trade(models.Model):
    portfolio = models.ForeignKey(Portfolio, related_name="trades", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    trade_type = models.CharField(max_length=4, choices=[("buy", "Buy"), ("sell", "Sell")])
    trade_price = models.FloatField()
    price_floor = models.FloatField(null=True, blank=True)
    price_ceiling = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trade_type.upper()} {self.quantity} {self.symbol} at ${self.trade_price}"

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, related_name="prices", on_delete=models.CASCADE)
    date = models.DateField()
    open_price = models.FloatField()
    close_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ("stock", "date")

    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"



class MockOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    order_type = models.CharField(max_length=4, choices=[("buy", "Buy"), ("sell", "Sell")])
    price_at_execution = models.FloatField()
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")], default="pending")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.order_type.upper()} {self.symbol} x{self.quantity} at ${self.price_at_execution}"



class PortfolioPerformance(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="performance")
    date = models.DateField(auto_now_add=True)
    total_value = models.FloatField()

    def __str__(self):
        return f"{self.portfolio.name} Performance on {self.date}"


class StockAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    target_price = models.FloatField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Alert for {self.symbol} at ${self.target_price}"



class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"