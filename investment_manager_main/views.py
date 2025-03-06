from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
import matplotlib.pyplot as plt
import io, base64
import pandas as pd
from .alpaca_api import get_stock_price, get_historical_data, place_mock_trade


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard') 

    return render(request, "investment_manager_main/home.html")


@login_required
def dashboard(request):
    return render(request, "investment_manager_main/dashboard.html", {"user": request.user})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)  # ✅ Free memory
    return base64.b64encode(buf.getvalue()).decode()


def stock_history(request):
    symbol = request.GET.get("symbol", "AAPL")  

    try:
        data = get_historical_data(symbol)
        if data.empty:
            raise ValueError("No data available for this stock.")  

        fig, ax = plt.subplots()
        ax.plot(data.index, data['close'], label=f"{symbol} Price", color='blue')
        ax.set_title(f"{symbol} Stock Price History")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price ($)")
        ax.legend()

        img_url = plot_to_base64(fig)  

        return render(request, "investment_manager_main/stock_history.html", {
            "img_url": img_url,
            "symbol": symbol
        })
    
    except Exception as e:
        error_message = f"Error retrieving stock data: {str(e)}"
        return render(request, "investment_manager_main/stock_history.html", {
            "error": error_message,
            "symbol": symbol
        })


def mock_trade(request):
    if request.method == "POST":
        symbol = request.POST.get("symbol", "").strip().upper()
        qty = request.POST.get("quantity")
        side = request.POST.get("side", "buy").lower()

        if not symbol:
            return render(request, "investment_manager_main/mock_trade.html", {"error": "Stock symbol is required."})

        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError("Quantity must be greater than zero.")

            order = place_mock_trade(symbol, qty, side)
            return render(request, "investment_manager_main/mock_trade.html", {"order": order})

        except ValueError as ve:
            return render(request, "investment_manager_main/mock_trade.html", {"error": str(ve)})

        except Exception as e:
            return render(request, "investment_manager_main/mock_trade.html", {"error": f"Trade failed: {str(e)}"})

    return render(request, "investment_manager_main/mock_trade.html")

    #hello
