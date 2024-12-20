from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from binance.client import Client
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import pandas as pd
import keys  # Import the credentials securely

# Initialize Binance Client
client = Client(keys.api, keys.secret)

# Initialize FastAPI app
app = FastAPI()

# Set up the templates directory
templates = Jinja2Templates(directory="templates")

# Serve static files under the "/static" endpoint
app.mount("/static", StaticFiles(directory="static"), name="static")


# Request model
class MarketRequest(BaseModel):
    symbol: str  # e.g., "BTCUSDT"
    interval: str = "1m"  # Default interval
    lookback_period: int = 200  # Default lookback period


def fetch_klines(symbol: str, interval: str, lookback_period: int):
    """
    Fetch historical candles for the given symbol and interval.
    """
    try:
        # Fetch klines data
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=lookback_period)
        # Create DataFrame
        df = pd.DataFrame(klines, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        # Process data
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['close'] = pd.to_numeric(df['close'])
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {e}")


def analyze_market(df):
    """
    Perform SMA and RSI-based analysis to give Buy/Sell signals.
    """
    # Calculate SMA
    sma_short = SMAIndicator(df['close'], window=50).sma_indicator()
    sma_long = SMAIndicator(df['close'], window=200).sma_indicator()
    df['sma_short'] = sma_short
    df['sma_long'] = sma_long

    # Calculate RSI
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()

    # Get the most recent values
    current_price = df['close'].iloc[-1]
    sma_short_val = df['sma_short'].iloc[-1]
    sma_long_val = df['sma_long'].iloc[-1]
    rsi_val = df['rsi'].iloc[-1]

    # Decision logic
    if sma_short_val > sma_long_val:  # Uptrend
        if rsi_val < 30:  # Oversold
            return "BUY (Trend is Up, RSI confirms)"
        else:
            return "BUY (Trend is Up)"
    elif sma_short_val < sma_long_val:  # Downtrend
        if rsi_val > 70:  # Overbought
            return "SELL (Trend is Down, RSI confirms)"
        else:
            return "SELL (Trend is Down)"
    else:
        return "HOLD (No clear trend)"


@app.get("/")
async def read_root(request: Request):
    """
    Render the index page (optional, can provide a form-based input).
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze/")
async def analyze_market_api(request: MarketRequest):
    """
    Analyze market and return prediction.
    """
    # Fetch market data
    data = fetch_klines(request.symbol, request.interval, request.lookback_period)
    if data.empty:
        raise HTTPException(status_code=404, detail="No market data found.")

    # Analyze the data
    prediction = analyze_market(data)
    return {"symbol": request.symbol, "prediction": prediction}
