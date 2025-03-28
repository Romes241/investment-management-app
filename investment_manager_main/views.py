
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import pandas as pd
from .alpaca_api import get_stock_price, get_historical_data
from .models import Portfolio, Holding, Trade, ContactMessage
from decimal import Decimal
from django.http import JsonResponse

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard') 
    return render(request, "home.html")



@login_required
def dashboard(request):
    portfolios = Portfolio.objects.filter(user=request.user)
    total_value = sum(p.total_value() for p in portfolios)  

    return render(request, "dashboard.html", {
        "user": request.user, 
        "portfolios": portfolios,
        "total_value": total_value,
        "no_portfolios": len(portfolios) == 0
    })
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def mock_trade(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

    if request.method == "POST":
        trade_type = request.POST.get("trade_type", "buy")
        symbol = request.POST.get("symbol", "").strip().upper()
        qty = request.POST.get("quantity")
        price_floor = request.POST.get("price_floor", None)
        price_ceiling = request.POST.get("price_ceiling", None)

        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError("Quantity must be greater than zero.")

            current_price = get_stock_price(symbol)
            if current_price is None:
                raise ValueError("Could not retrieve stock price.")

            total_value = qty * current_price
            price_floor = float(price_floor) if price_floor and price_floor.strip() else None
            price_ceiling = float(price_ceiling) if price_ceiling and price_ceiling.strip() else None

            if price_floor and price_floor > current_price:
                raise ValueError("Price floor must be lower than the current price.")
            if price_ceiling and price_ceiling < current_price:
                raise ValueError("Price ceiling must be higher than the current price.")
            if price_floor and price_ceiling and price_floor >= price_ceiling:
                raise ValueError("Price floor must be less than price ceiling.")

            if trade_type == "buy":
                if portfolio.balance < total_value:
                    raise ValueError("Insufficient funds for this trade.")
                portfolio.balance -= Decimal(str(total_value))
            elif trade_type == "sell":
                holding = Holding.objects.filter(portfolio=portfolio, symbol=symbol).first()
                if not holding or holding.quantity < qty:
                    raise ValueError("You do not have enough shares to sell.")
                portfolio.balance += Decimal(str(total_value))
                holding.quantity -= qty
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.save()
            else:
                raise ValueError("Invalid trade type.")

            portfolio.save()

            Trade.objects.create(
                portfolio=portfolio,
                symbol=symbol,
                quantity=qty,
                trade_type=trade_type,
                trade_price=current_price,
                price_floor=price_floor,
                price_ceiling=price_ceiling
            )

            if trade_type == "buy":
                holding, created = Holding.objects.get_or_create(
                    portfolio=portfolio,
                    symbol=symbol,
                    defaults={"quantity": qty, "average_price": current_price}
                )
                if not created:
                    total_shares = holding.quantity + qty
                    new_avg = ((holding.average_price * holding.quantity) + (current_price * qty)) / total_shares
                    holding.quantity = total_shares
                    holding.average_price = new_avg
                    holding.save()

            return redirect("portfolio_details", portfolio_id=portfolio.id)

        except ValueError as ve:
            return render(request, "mock_trade.html", {
                "error": str(ve),
                "portfolio": portfolio
            })

    return render(request, "mock_trade.html", {"portfolio": portfolio})


@login_required
def create_portfolio(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        balance = request.POST.get("balance", "").strip()

        if not name:
            return render(request, "create_portfolio.html", {"error": "Portfolio name is required."})
        if not balance or float(balance) < 0:
            return render(request, "create_portfolio.html", {"error": "Initial balance must be a positive number."})

        Portfolio.objects.create(user=request.user, name=name, balance=float(balance))
        return redirect("dashboard")

    return render(request, "create_portfolio.html")

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})

@login_required
def portfolio_details(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    holdings = portfolio.holdings.all()
    trades = portfolio.trades.all()

    trade_symbols = list(trades.values_list("symbol", flat=True))
    trade_quantity = list(trades.values_list("quantity", flat=True))


    for holding in holdings:
        holding.current_price = get_stock_price(holding.symbol)
        holding.current_value = holding.current_price * holding.quantity if holding.current_price else 0

    context = {
        "portfolio": portfolio,
        "holdings": holdings,
        "trades": trades,
        "balance": portfolio.balance,
        "total_invested": portfolio.total_invested(),  
        "total_profit_loss": portfolio.total_profit_loss(),  
        "gains_percentage": portfolio.gains_percentage(), 
        "trade_symbols":trade_symbols,
        "trade_quantity":trade_quantity, 

    }

    return render(request, "portfolio_details.html", context)

def portfolio_statistics_view(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

    context = {
        'portfolio': portfolio,
        'balance': portfolio.balance,
        'total_invested': portfolio.total_invested(), 
        'total_profit_loss': portfolio.total_profit_loss(),
        'gains_percentage': portfolio.gains_percentage(),
    }
    
    
    return render(request, 'portfolio_details.html', context)

@login_required
def delete_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

    if request.method == "POST":
        portfolio.delete()
        return redirect("dashboard")

    return render(request, "confirm_delete.html", {"portfolio": portfolio})

@login_required
def get_stock_price_view(request):
    symbol = request.GET.get("symbol", "").strip().upper()
    if not symbol:
        return JsonResponse({"error": "Stock symbol is required."}, status=400)

    price = get_stock_price(symbol)
    if price is None:
        return JsonResponse({"error": "Could not retrieve stock price."}, status=404)

    return JsonResponse({"symbol": symbol, "price": price})

@login_required
def get_user_holding(request):
    symbol = request.GET.get("symbol", "").strip().upper()
    portfolio = Portfolio.objects.filter(user=request.user).first()

    if not portfolio or not symbol:
        return JsonResponse({"quantity": 0})

    holding = Holding.objects.filter(portfolio=portfolio, symbol=symbol).first()
    if holding:
        return JsonResponse({"quantity": holding.quantity})
    return JsonResponse({"quantity": 0})

@login_required
def get_stock_history(request):
    symbol = request.GET.get("symbol", "").upper()
    timeframe = request.GET.get("timeframe", "1Y")

    timeframe_days = {
        "1D": 1,
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365
    }.get(timeframe, 365)

    try:
        df = get_historical_data(symbol, days=timeframe_days)
        if df is None or df.empty:
            raise ValueError("No historical data found.")

        df = df.sort_index()
        return JsonResponse({
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "prices": df['close'].tolist()
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def about(request):
    return render(request, "about.html")

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            return render(request, "contact_us.html", {"success": True})

    return render(request, "contact_us.html")

@login_required
def stock_search(request):
    return render(request, "stock_search.html")

@login_required
def stock_history_display(request, symbol):
    timeframe = request.GET.get("timeframe", "1Y")
    timeframe_days = {
        "1D": 1, "1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365
    }.get(timeframe, 365)

    history = get_historical_data(symbol, days=timeframe_days)
    if history is None or history.empty:
        return render(request, "stock_history.html", {
            "symbol": symbol,
            "error": "No data available for this stock."
        })

    metrics = {
        "open": round(history['open'].iloc[-1], 2),
        "high": round(history['high'].max(), 2),
        "low": round(history['low'].min(), 2),
        "volume": int(history['volume'].sum()),
    }

    dates = history.index.strftime('%Y-%m-%d').tolist()
    prices = history['close'].tolist()

    return render(request, "stock_history.html", {
        "symbol": symbol,
        "company_name": f"{symbol} Inc",
        "overview": f"{symbol} is a major company in the industry.",
        "metrics": metrics,
        "dates": dates,
        "prices": prices,
        "initial_timeframe": timeframe
    })

def external_information(request):
    return render(request, "external_information.html")
