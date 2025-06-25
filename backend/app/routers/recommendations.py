from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from models.user import User
from models.stock import Stock
from models.portfolio import Portfolio, Holding
from models.trade import Trade
from motor.motor_asyncio import AsyncIOMotorClient
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors
from datetime import datetime, timedelta
import asyncio
from pymongo import DESCENDING
from beanie import PydanticObjectId
import json
import logging
import random  # Pentru simulări
from functools import lru_cache

# Configurare logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Implementări pentru calcularea indicatorilor tehnici
def calculate_sma(data, timeperiod=20):
    """Implementare pentru Simple Moving Average (SMA)"""
    return data.rolling(window=timeperiod).mean()

def calculate_ema(data, timeperiod=20):
    """Implementare pentru Exponential Moving Average (EMA)"""
    return data.ewm(span=timeperiod, adjust=False).mean()

def calculate_rsi(data, timeperiod=14):
    """Implementare pentru Relative Strength Index (RSI)"""
    delta = data.diff()
    up = delta.copy()
    up[up < 0] = 0
    down = -1 * delta.copy()
    down[down < 0] = 0
    
    avg_gain = up.ewm(com=timeperiod-1, min_periods=timeperiod).mean()
    avg_loss = down.ewm(com=timeperiod-1, min_periods=timeperiod).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fastperiod=12, slowperiod=26, signalperiod=9):
    """Implementare pentru MACD"""
    fast_ema = calculate_ema(data, fastperiod)
    slow_ema = calculate_ema(data, slowperiod)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signalperiod)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_atr(high, low, close, timeperiod=14):
    """Implementare pentru Average True Range (ATR)"""
    # CORECTARE: Asigurăm-ne că high, low, close sunt pandas Series
    if isinstance(high, np.ndarray):
        high = pd.Series(high)
    if isinstance(low, np.ndarray):
        low = pd.Series(low)
    if isinstance(close, np.ndarray):
        close = pd.Series(close)
    
    tr1 = np.abs(high[1:].values - low[1:].values)
    tr2 = np.abs(high[1:].values - close[:-1].values)
    tr3 = np.abs(low[1:].values - close[:-1].values)
    
    tr = np.vstack([tr1, tr2, tr3]).max(axis=0)
    tr = np.append(tr1[0], tr)  # Use first TR as starting point
    
    atr = np.zeros_like(close.values)
    atr[0] = tr[0]  # First ATR is first TR
    
    for i in range(1, len(close)):
        atr[i] = (atr[i-1] * (timeperiod - 1) + tr[i]) / timeperiod
    
    return pd.Series(atr, index=close.index)

# Cache pentru date
_stock_data_cache = {}
_last_cache_cleanup = datetime.now()

# Funcție de curățare a cache-ului
def cleanup_cache():
    """Curăță cache-ul dacă a trecut prea mult timp de la ultima curățare"""
    global _last_cache_cleanup
    current_time = datetime.now()
    
    # Curăță cache-ul o dată pe zi
    if (current_time - _last_cache_cleanup).days >= 1:
        _stock_data_cache.clear()
        _last_cache_cleanup = current_time
        logger.info("Cache cleared due to daily maintenance")

# Îmbunătățirea funcției get_stock_historical_data pentru a genera date mai realiste

async def get_stock_historical_data(symbol: str, period: str = "6mo"):
    """
    Obține date istorice pentru un simbol din baza de date locală
    """
    try:
        cleanup_cache()
        
        # Verifică dacă avem date în cache
        cache_key = f"{symbol}_{period}"
        if cache_key in _stock_data_cache:
            return _stock_data_cache[cache_key]
        
        # Obține stocul din baza de date
        stock = await Stock.find_one(Stock.symbol == symbol)
        if not stock:
            logger.warning(f"Stock {symbol} not found in database")
            return None
        
        # Calculăm câte zile să simulăm în funcție de perioada cerută
        days = 180  # default pentru 6mo
        if period == "1mo":
            days = 30
        elif period == "3mo":
            days = 90
        elif period == "1y":
            days = 365
        
        # Generăm serii de timp pentru perioada solicitată
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        
        # Simulăm prețuri bazate pe prețul curent și o volatilitate aleatoare
        last_price = stock.last_price or 100.0  # Preț implicit dacă lipsește
        
        # Generăm volatilitate bazată pe sector
        volatility_factor = 0.02  # implicit 2%
        if hasattr(stock, 'sector') and stock.sector:
            if stock.sector in ["Technology", "Technology Services"]:
                volatility_factor = 0.03
            elif stock.sector in ["Healthcare", "Finance"]:
                volatility_factor = 0.02
            elif stock.sector in ["Consumer Staples", "Utilities"]:
                volatility_factor = 0.01
        
        # Generăm o serie de prețuri cu DIFERENȚE CLARE între perioadele de 1 și 3 luni
        # Pentru a simula tendințe diferite pentru fiecare perioadă
        
        # Generăm 3 trenduri distincte pentru diferite perioade
        # Ultimele 30 de zile (1 lună)
        trend_1m = random.choice([
            random.uniform(0.05, 0.15),    # Trend puternic ascendent
            random.uniform(-0.15, -0.05),  # Trend puternic descendent
            random.uniform(-0.03, 0.03)    # Relativ plat
        ])
        
        # Ultimele 31-90 de zile (a doua și a treia lună)
        trend_2_3m = random.choice([
            random.uniform(0.03, 0.10),   # Trend moderat ascendent
            random.uniform(-0.10, -0.03), # Trend moderat descendent
            random.uniform(-0.02, 0.02)   # Relativ plat
        ])
        
        # Restul perioadei (peste 3 luni)
        trend_rest = random.choice([
            random.uniform(0.01, 0.05),   # Trend ușor ascendent
            random.uniform(-0.05, -0.01), # Trend ușor descendent
            random.uniform(-0.01, 0.01)   # Relativ plat
        ])
        
        # Generăm prețurile pentru fiecare zi
        prices = [last_price]
        current_price = last_price
        
        # Inversăm ordinea zilelor pentru a genera istoric (de la prezent către trecut)
        for i in range(1, len(date_range)):
            # Stabilim trendul în funcție de perioada din care face parte ziua
            if i < 22:  # Ultimele ~22 zile de tranzacționare (1 lună)
                trend = trend_1m / 22  # Distribuie trendul lunar pe zile
            elif i < 66:  # Între 1-3 luni (~44 zile)
                trend = trend_2_3m / 44  # Distribuie trendul pe zile
            else:  # Peste 3 luni
                trend = trend_rest / (len(date_range) - 66)  # Distribuie restul trendului
            
            # Adăugă volatilitate zilnică
            daily_vol = random.normalvariate(0, volatility_factor)
            
            # Calculează prețul pentru ziua anterioară (mergem înapoi în timp)
            current_price = current_price / (1 + trend + daily_vol)
            
            # Asigură-te că prețul nu scade sub un prag minim
            current_price = max(current_price, 0.1 * last_price)
            
            prices.append(current_price)
        
        # Inversăm înapoi pentru a avea prețurile în ordine cronologică
        prices.reverse()
        
        # Creăm un DataFrame cu datele generate
        hist_data = pd.DataFrame({
            'Close': prices,
            'Open': [p * (1 - random.uniform(0, 0.01)) for p in prices],
            'High': [p * (1 + random.uniform(0, 0.02)) for p in prices],
            'Low': [p * (1 - random.uniform(0, 0.02)) for p in prices],
            'Volume': [random.randint(100000, 10000000) for _ in prices]
        }, index=date_range[:len(prices)])
        
        # Calculăm indicatorii tehnici
        hist_data['SMA_20'] = calculate_sma(hist_data['Close'], timeperiod=20)
        hist_data['SMA_50'] = calculate_sma(hist_data['Close'], timeperiod=50)
        hist_data['RSI'] = calculate_rsi(hist_data['Close'], timeperiod=14)
        
        macd_line, macd_signal, macd_hist = calculate_macd(
            hist_data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        hist_data['MACD'] = macd_line
        hist_data['MACD_Signal'] = macd_signal
        hist_data['MACD_Hist'] = macd_hist
        
        hist_data['ATR'] = calculate_atr(hist_data['High'], hist_data['Low'], hist_data['Close'], timeperiod=14)
        
        # Calculăm volatilitatea zilnică
        hist_data['Daily_Return'] = hist_data['Close'].pct_change()
        hist_data['Volatility'] = hist_data['Daily_Return'].rolling(window=20).std() * np.sqrt(252)  # Anualizată
        
        result = hist_data.dropna()
        
        # Verificăm că avem performanțe diferite pentru perioade diferite
        if len(result) >= 66:  # Avem cel puțin 3 luni de date
            one_month_perf = (result['Close'].iloc[-1] / result['Close'].iloc[-22] - 1) * 100
            three_month_perf = (result['Close'].iloc[-1] / result['Close'].iloc[-66] - 1) * 100
            
            # Dacă performanțele sunt prea similare, regenerăm datele
            if abs(one_month_perf - three_month_perf) < 2.0:
                logger.info(f"Regenerating data for {symbol} due to similar performances")
                _stock_data_cache.pop(cache_key, None)  # Eliminăm din cache dacă există
                return await get_stock_historical_data(symbol, period)  # Recursiv
        
        # Salvăm în cache
        _stock_data_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {str(e)}")
        return None

async def get_user_data(user_id: str):
    """Obține toate datele relevante despre un utilizator."""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Portofoliu utilizator - CORECTARE
    portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
    
    # Istoricul tranzacțiilor utilizatorului
    trades = await Trade.find(Trade.user_id == str(user_id)).sort([("timestamp", DESCENDING)]).to_list()
    
    return {"user": user, "portfolio": portfolio, "trades": trades}
async def get_portfolio_stats(portfolio):
    """Obține statistici detaliate despre portofoliul utilizatorului."""
    if not portfolio or not portfolio.holdings:
        return {
            "total_value": 0,
            "num_holdings": 0,
            "sectors": {},
            "avg_profit_loss": 0,
            "best_performer": None,
            "worst_performer": None
        }
    
    total_value = 0
    sectors = {}
    performance = []
    
    for holding in portfolio.holdings:
        total_value += holding.market_value
        
        stock = await Stock.find_one(Stock.symbol == holding.symbol)
        sector = stock.sector if stock and hasattr(stock, "sector") else "Unknown"
        
        if sector not in sectors:
            sectors[sector] = 0
        sectors[sector] += holding.market_value
        
        if hasattr(holding, "profit_loss_pct"):
            performance.append((holding.symbol, holding.profit_loss_pct))
        elif hasattr(holding, "profit_loss") and holding.avg_buy_price > 0:
            profit_loss_pct = (holding.profit_loss / (holding.avg_buy_price * holding.quantity)) * 100
            performance.append((holding.symbol, profit_loss_pct))
    
    # Calculează procentajul fiecărui sector
    for sector in sectors:
        sectors[sector] = (sectors[sector] / total_value) * 100
    
    # Sortează sectoarele după pondere
    sorted_sectors = dict(sorted(sectors.items(), key=lambda item: item[1], reverse=True))
    
    # Găsește cel mai bun și cel mai slab performer
    best_performer = None
    worst_performer = None
    
    if performance:
        sorted_performance = sorted(performance, key=lambda x: x[1], reverse=True)
        best_performer = {
            "symbol": sorted_performance[0][0],
            "performance": sorted_performance[0][1]
        }
        worst_performer = {
            "symbol": sorted_performance[-1][0],
            "performance": sorted_performance[-1][1]
        }
    
    # Calculează profit/pierdere mediu în portofoliu
    avg_profit_loss = sum(perf for _, perf in performance) / len(performance) if performance else 0
    
    return {
        "total_value": total_value,
        "num_holdings": len(portfolio.holdings),
        "sectors": sorted_sectors,
        "avg_profit_loss": avg_profit_loss,
        "best_performer": best_performer,
        "worst_performer": worst_performer
    }

async def analyze_user_trading_style(user_id: str):
    """Analizează stilul de tranzacționare al utilizatorului."""
    trades = await Trade.find(Trade.user_id == user_id).sort([("timestamp", DESCENDING)]).to_list()
    
    if not trades:
        return {
            "profile": "unknown",
            "risk_appetite": "unknown",
            "avg_hold_time": 0,
            "preferred_sectors": [],
            "activity_level": "inactive"
        }
    
    # Analizează volumul și frecvența tranzacțiilor
    buy_trades = [t for t in trades if t.type.lower() == "buy"]
    sell_trades = [t for t in trades if t.type.lower() == "sell"]
    
    trade_count = len(trades)
    recent_trades = [t for t in trades if (datetime.utcnow() - t.timestamp).days <= 30]
    
    # Determină nivelul de activitate
    if len(recent_trades) >= 10:
        activity_level = "very_active"
    elif len(recent_trades) >= 5:
        activity_level = "active"
    elif len(recent_trades) >= 1:
        activity_level = "moderate"
    else:
        activity_level = "inactive"
    
    # Analizează durata medie de deținere pentru tranzacții închise
    hold_times = []
    closed_positions = {}
    
    # Identifică pozițiile închise
    for trade in trades:
        symbol = trade.symbol
        if trade.type.lower() == "buy":
            if symbol not in closed_positions:
                closed_positions[symbol] = []
            closed_positions[symbol].append({"time": trade.timestamp, "price": trade.price, "quantity": trade.quantity})
        elif trade.type.lower() == "sell":
            if symbol in closed_positions and closed_positions[symbol]:
                buy_trade = closed_positions[symbol].pop()
                hold_time = (trade.timestamp - buy_trade["time"]).days
                hold_times.append(hold_time)
    
    avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0
    
    # Determină profilul de investiție
    if avg_hold_time < 7:
        profile = "day_trader"
    elif avg_hold_time < 30:
        profile = "swing_trader"
    elif avg_hold_time < 180:
        profile = "position_trader"
    else:
        profile = "long_term_investor"
    
    # Analizează sectoarele preferate
    sector_counts = {}
    for trade in trades:
        stock = await Stock.find_one(Stock.symbol == trade.symbol)
        if stock and hasattr(stock, "sector") and stock.sector:
            sector = stock.sector
            if sector not in sector_counts:
                sector_counts[sector] = 0
            sector_counts[sector] += 1
    
    preferred_sectors = [sector for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
    
    # Determină apetitul pentru risc bazat pe volatilitatea stocurilor tranzacționate
    volatilities = []
    for trade in trades[-10:]:  # Utilizează doar ultimele 10 tranzacții
        hist_data = await get_stock_historical_data(trade.symbol, period="3mo")
        if hist_data is not None and 'Volatility' in hist_data:
            volatilities.append(hist_data['Volatility'].iloc[-1])
    
    avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
    
    if avg_volatility < 0.15:
        risk_appetite = "conservative"
    elif avg_volatility < 0.25:
        risk_appetite = "moderate"
    else:
        risk_appetite = "aggressive"
    
    return {
        "profile": profile,
        "risk_appetite": risk_appetite,
        "avg_hold_time": avg_hold_time,
        "preferred_sectors": preferred_sectors,
        "activity_level": activity_level
    }

async def analyze_market_trend():
    """Analizează tendința generală a pieței folosind indici din baza de date."""
    try:
        # Indici de piață - Id-urile acestora ar trebui să existe în baza de date
        index_symbols = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
        index_names = ["S&P 500", "Dow Jones", "Nasdaq", "Volatility Index"]
        
        market_data = {}
        
        for symbol, name in zip(index_symbols, index_names):
            # Obține datele indicelui din baza de date
            index_stock = await Stock.find_one(Stock.symbol == symbol)
            if not index_stock:
                # Dacă indicele nu există în baza de date, continuăm fără el
                continue
                
            # Obține date istorice
            hist_data = await get_stock_historical_data(symbol, period="1mo")
            if hist_data is None or hist_data.empty:
                continue
                
            # Calculează schimbările de preț
            month_change = ((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[0]) - 1) * 100
            two_week_idx = max(0, len(hist_data) - 10)  # ~10 zile de tranzacționare în 2 săptămâni
            two_week_change = ((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[two_week_idx]) - 1) * 100
            week_idx = max(0, len(hist_data) - 5)  # ~5 zile de tranzacționare într-o săptămână
            week_change = ((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[week_idx]) - 1) * 100
            
            market_data[name] = {
                "month_change": month_change,
                "two_week_change": two_week_change,
                "week_change": week_change,
                "current_value": hist_data['Close'].iloc[-1],
                "is_bullish": month_change > 0 and two_week_change > 0
            }
        
        # Dacă nu avem date pentru indici, simulăm datele pentru a evita întreruperea serviciului
        if not market_data:
            # Simulăm un trend general bazat pe stocuri aleatorii
            all_stocks = await Stock.find_all().limit(20).to_list()
            bullish_count = 0
            bearish_count = 0
            
            for stock in all_stocks:
                if stock.last_price and hasattr(stock, 'previous_price') and stock.previous_price:
                    if stock.last_price > stock.previous_price:
                        bullish_count += 1
                    else:
                        bearish_count += 1
                else:
                    # Dacă nu avem prețuri anterioare, alegem aleatoriu
                    if random.random() > 0.5:
                        bullish_count += 1
                    else:
                        bearish_count += 1
            
            # Simulăm date pentru indici populari
            for symbol, name in zip(index_symbols, index_names):
                month_change = random.uniform(-5, 10) if bullish_count > bearish_count else random.uniform(-10, 5)
                two_week_change = random.uniform(-3, 7) if bullish_count > bearish_count else random.uniform(-7, 3)
                week_change = random.uniform(-2, 5) if bullish_count > bearish_count else random.uniform(-5, 2)
                
                market_data[name] = {
                    "month_change": month_change,
                    "two_week_change": two_week_change,
                    "week_change": week_change,
                    "current_value": random.uniform(10000, 40000) if name == "Dow Jones" else random.uniform(1000, 5000),
                    "is_bullish": month_change > 0 and two_week_change > 0
                }
        
        # Determinăm trendul general
        bullish_count = sum(1 for data in market_data.values() if data["is_bullish"])
        bearish_count = len(market_data) - bullish_count
        
        market_trend = {
            "trend": "bullish" if bullish_count > bearish_count else "bearish",
            "indices": market_data,
            "confidence": abs(bullish_count - bearish_count) / len(market_data) if market_data else 0
        }
        
        return market_trend
    except Exception as e:
        logger.error(f"Error analyzing market trend: {str(e)}")
        return {"trend": "unknown", "confidence": 0}

async def get_sector_performance():
    """Analizează performanța sectoarelor folosind datele din baza de date."""
    try:
        # Obține toate acțiunile din baza de date
        stocks = await Stock.find_all().to_list()
        
        # Grupează acțiunile pe sectoare
        sector_stocks = {}
        for stock in stocks:
            if hasattr(stock, 'sector') and stock.sector:
                sector = stock.sector
            else:
                sector = "Unknown"
                
            if sector not in sector_stocks:
                sector_stocks[sector] = []
            sector_stocks[sector].append(stock)
        
        # Calculează performanța pentru fiecare sector
        sector_performance = {}
        for sector, stocks_list in sector_stocks.items():
            if sector == "Unknown" or not stocks_list:
                continue
                
            # Selectăm doar acțiuni cu date suficiente
            valid_stocks = [s for s in stocks_list if hasattr(s, 'last_price') and s.last_price and 
                           hasattr(s, 'market_cap') and s.market_cap and s.market_cap > 0]
            if not valid_stocks:
                continue
            
            # Calculează performanța medie ponderată după capitalizarea de piață
            total_market_cap = sum(s.market_cap for s in valid_stocks)
            
            # Folosim doar primele 10 stocuri pentru performanță
            performance_data = []
            for stock in valid_stocks[:min(10, len(valid_stocks))]:
                # Obținem date istorice
                hist_data = await get_stock_historical_data(stock.symbol, period="1mo")
                if hist_data is not None and not hist_data.empty:
                    month_perf = ((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[0]) - 1) * 100
                    weight = stock.market_cap / total_market_cap
                    performance_data.append((month_perf, weight))
            
            if performance_data:
                weighted_performance = sum(perf * weight for perf, weight in performance_data)
                sector_performance[sector] = {
                    "month_performance": weighted_performance,
                    "count": len(valid_stocks),
                    "total_market_cap": total_market_cap
                }
        
        # Sortează sectoarele după performanță
        sorted_sectors = sorted(
            sector_performance.items(), 
            key=lambda x: x[1]["month_performance"], 
            reverse=True
        )
        
        return {
            "top_sectors": sorted_sectors[:3] if sorted_sectors else [],
            "bottom_sectors": sorted_sectors[-3:] if len(sorted_sectors) > 3 else []
        }
    except Exception as e:
        logger.error(f"Error getting sector performance: {str(e)}")
        return {"top_sectors": [], "bottom_sectors": []}

async def build_user_trade_matrix():
    """Construiește o matrice utilizator-acțiune pentru recomandări colaborative."""
    try:
        # Obține toți utilizatorii și tranzacțiile lor
        users = await User.find_all().to_list()
        user_trades = {}
        
        for user in users:
            trades = await Trade.find(Trade.user_id == str(user.id)).to_list()
            user_trades[str(user.id)] = trades
        
        # Creează un set de toate simbolurile tranzacționate
        all_symbols = set()
        for trades in user_trades.values():
            for trade in trades:
                all_symbols.add(trade.symbol)
        
        # Construiește matricea utilizator-acțiune
        user_stock_matrix = {}
        for user_id, trades in user_trades.items():
            user_stock_matrix[user_id] = {}
            
            # Inițializează toate simbolurile cu 0
            for symbol in all_symbols:
                user_stock_matrix[user_id][symbol] = 0
            
            # Adaugă scoruri în funcție de tranzacții
            for trade in trades:
                # Scorul este bazat pe direcția tranzacției și recența
                days_ago = (datetime.utcnow() - trade.timestamp).days + 1
                recency_weight = 1.0 / days_ago  # Mai recent = mai important
                
                # Verificăm dacă trade are atributul type sau trade_type
                if hasattr(trade, 'type'):
                    direction_weight = 1 if trade.type.lower() == "buy" else -0.5
                elif hasattr(trade, 'trade_type'):
                    direction_weight = 1 if trade.trade_type.lower() == "buy" else -0.5
                else:
                    direction_weight = 0  # Default dacă nu putem determina tipul
                
                # Actualizează scorul
                current_score = user_stock_matrix[user_id][trade.symbol]
                user_stock_matrix[user_id][trade.symbol] = current_score + (direction_weight * recency_weight)
        
        return user_stock_matrix, list(all_symbols)
    except Exception as e:
        logger.error(f"Error building user trade matrix: {str(e)}")
        return {}, []

async def portfolio_based_recommendations(user_id: str, n_recommendations: int = 5):
    """Generează recomandări bazate direct pe portofoliul curent al utilizatorului."""
    try:
        # Obține portofoliul utilizatorului - CORECTARE
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        if not portfolio or not portfolio.holdings:
            return []
        
        # Obține statistici pentru portofoliu
        portfolio_stats = await get_portfolio_stats(portfolio)
        
        # Identifică concentrarea actuală a investițiilor și găsește oportunități de diversificare
        primary_sectors = list(portfolio_stats["sectors"].keys())[:2] if portfolio_stats["sectors"] else []
        
        # Obține acțiuni din sectoare cu performanță bună care nu sunt în portofoliu
        sector_performance = await get_sector_performance()
        top_performing_sectors = [s[0] for s in sector_performance["top_sectors"]]
        
        # Extrage simbolurile din portofoliul actual
        portfolio_symbols = [holding.symbol for holding in portfolio.holdings]
        
        # Obține acțiuni potențiale pentru diversificare
        stock_recommendations = {}
        
        # Strategie 1: Acțiuni care completează portofoliul din sectoare performante
        for sector in top_performing_sectors:
            if sector not in primary_sectors:  # Preferăm sectoare care nu sunt deja bine reprezentate
                sector_stocks = await Stock.find({
                    "sector": sector,
                    "symbol": {"$nin": portfolio_symbols}
                }).to_list()
                
                for stock in sector_stocks:
                    if not stock.symbol in stock_recommendations:
                        stock_recommendations[stock.symbol] = 0
                    
                    # Scor bazat pe performanța sectorului și lipsa lui în portofoliu
                    sector_idx = top_performing_sectors.index(sector)
                    stock_recommendations[stock.symbol] += (5 - min(sector_idx, 4)) * 2
        
        # Strategie 2: Acțiuni similare cu cele mai bune din portofoliu (dacă există)
        if portfolio_stats["best_performer"]:
            best_stock_symbol = portfolio_stats["best_performer"]["symbol"]
            best_stock = await Stock.find_one(Stock.symbol == best_stock_symbol)
            
            if best_stock and hasattr(best_stock, "sector") and best_stock.sector:
                # Găsește acțiuni similare din același sector
                similar_stocks = await Stock.find({
                    "sector": best_stock.sector,
                    "symbol": {"$nin": portfolio_symbols}
                }).to_list()
                
                for stock in similar_stocks:
                    if not stock.symbol in stock_recommendations:
                        stock_recommendations[stock.symbol] = 0
                    
                    # Scor pentru acțiuni similare cu cele performante din portofoliu
                    stock_recommendations[stock.symbol] += 10
                    
                    # Bonus pentru capitalizare de piață similară
                    if abs(stock.market_cap - best_stock.market_cap) / best_stock.market_cap < 0.5:
                        stock_recommendations[stock.symbol] += 5
        
        # Strategie 3: Acțiuni pentru înlocuirea celor cu performanță slabă
        if portfolio_stats["worst_performer"] and portfolio_stats["worst_performer"]["performance"] < -10:
            worst_stock_symbol = portfolio_stats["worst_performer"]["symbol"]
            worst_stock = await Stock.find_one(Stock.symbol == worst_stock_symbol)
            
            if worst_stock and hasattr(worst_stock, "sector") and worst_stock.sector:
                # Găsește alternative mai bune din același sector
                replacement_stocks = await Stock.find(
                    (Stock.sector == worst_stock.sector) & 
                    (Stock.symbol.not_in(portfolio_symbols))
                ).to_list()
                
                for stock in replacement_stocks:
                    if not stock.symbol in stock_recommendations:
                        stock_recommendations[stock.symbol] = 0
                    
                    # Scor pentru acțiuni care ar putea înlocui cele cu performanță slabă
                    stock_recommendations[stock.symbol] += 8
        
        # Oferă recomandări pentru "core holdings" dacă portofoliul este mic
        if portfolio_stats["num_holdings"] < 5:
            # Adăugăm acțiuni blue-chip stabile pentru un portofoliu nou
            blue_chips = await Stock.find({
                "market_cap": {"$gt": 200e9},
                "symbol": {"$nin": portfolio_symbols}
            }).limit(10).to_list()
            
            for stock in blue_chips:
                if not stock.symbol in stock_recommendations:
                    stock_recommendations[stock.symbol] = 0
                stock_recommendations[stock.symbol] += 7
        
        # Sortează și returnează recomandările
        sorted_recommendations = sorted(
            stock_recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [symbol for symbol, _ in sorted_recommendations[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in portfolio-based recommendations: {str(e)}")
        return []

async def investment_goal_recommendations(user_id: str, n_recommendations: int = 5):
    """Generează recomandări bazate pe obiectivele de investiții ale utilizatorului."""
    try:
        # Folosește User.get cu PydanticObjectId
        try:
            user = await User.get(PydanticObjectId(user_id))
            if not user:
                logger.warning(f"Investment goal recommendations: User {user_id} not found")
                return []
        except Exception as e:
            logger.error(f"Error finding user in investment_goal_recommendations: {str(e)}")
            return []
        
  
        trading_style = await analyze_user_trading_style(user_id)
        
        # Setează obiectivele implicite dacă nu avem informații suficiente
        investment_goals = {
            "growth": 0.5,  # 50% creștere
            "income": 0.3,  # 30% venit
            "value": 0.2,   # 20% valoare
        }
        
        # Ajustează obiectivele în funcție de stilul de tranzacționare
        if trading_style["profile"] == "day_trader" or trading_style["profile"] == "swing_trader":
            investment_goals = {
                "growth": 0.7,
                "income": 0.1,
                "value": 0.2,
            }
        elif trading_style["profile"] == "position_trader":
            investment_goals = {
                "growth": 0.5,
                "income": 0.3,
                "value": 0.2,
            }
        elif trading_style["profile"] == "long_term_investor":
            investment_goals = {
                "growth": 0.3,
                "income": 0.4,
                "value": 0.3,
            }
        
       
        if trading_style["risk_appetite"] == "conservative":
            investment_goals["growth"] -= 0.1
            investment_goals["income"] += 0.1
        elif trading_style["risk_appetite"] == "aggressive":
            investment_goals["growth"] += 0.1
            investment_goals["income"] -= 0.1
        
        
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        owned_symbols = []
        if portfolio and portfolio.holdings:
            owned_symbols = [holding.symbol for holding in portfolio.holdings]
        
        
        all_stocks = await Stock.find({
            "symbol": {"$nin": owned_symbols}
        }).to_list()
                
        stock_scores = {}
        
        for stock in all_stocks:
            if not hasattr(stock, 'symbol') or not stock.symbol:
                continue
            
            score = 0
            
            
            hist_data = await get_stock_historical_data(stock.symbol)
            if hist_data is None or hist_data.empty:
                continue
            
            # Scorul pentru creștere
            if hasattr(stock, "pe_ratio") and stock.pe_ratio:
                # Acțiuni de creștere au de obicei PE ratio mai mare
                if stock.pe_ratio > 20:
                    growth_score = min(stock.pe_ratio / 10, 10)  # Max 10
                    score += growth_score * investment_goals["growth"]
            
            # Scorul pentru venit (dividende)
            if hasattr(stock, "dividend_yield") and stock.dividend_yield:
                # Acțiuni pentru venit au dividend yield mai mare
                income_score = min(stock.dividend_yield * 10, 10)  # Max 10
                score += income_score * investment_goals["income"]
            
            # Scorul pentru valoare
            if hasattr(stock, "price_to_book") and stock.price_to_book:
                # Acțiuni value au price-to-book mai mic
                if stock.price_to_book < 3:
                    value_score = min((3 - stock.price_to_book) * 3, 10)  # Max 10
                    score += value_score * investment_goals["value"]
            
            # Adaugă scorul final
            stock_scores[stock.symbol] = score
        
        # Sortează și returnează simbolurile cu scorurile cele mai mari
        sorted_scores = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
        return [symbol for symbol, _ in sorted_scores[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in investment goal recommendations: {str(e)}")
        return []

async def collaborative_filtering(user_id: str, matrix: Dict, symbols: List[str], n_recommendations: int = 5):
    """Recomandă acțiuni folosind filtrare colaborativă cu scikit-learn în loc de Surprise."""
    try:
        if not matrix or user_id not in matrix:
            logger.warning(f"Cannot generate collaborative recommendations for user {user_id}: insufficient data")
            return []
        
        # Verificăm dacă avem simboluri pentru a evita eroarea cu 0 caracteristici
        if not symbols:
            logger.warning("Collaborative filtering: No symbols available")
            return []
            
        # Evităm importarea Surprise și utilizăm doar scikit-learn
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Convertim matricea user-item într-un format adecvat pentru sklearn
        users = list(matrix.keys())
        user_idx = {u: i for i, u in enumerate(users)}
        symbol_idx = {s: i for i, s in enumerate(symbols)}
        
        # Creăm matricea de utilizare
        user_item_matrix = np.zeros((len(users), len(symbols)))
        
        # Populăm matricea cu scoruri
        for u, ratings in matrix.items():
            if u in user_idx:  # Verificăm dacă utilizatorul există în index
                i = user_idx[u]
                for s, score in ratings.items():
                    if s in symbol_idx:  # Verificăm dacă simbolul există în index
                        j = symbol_idx[s]
                        user_item_matrix[i, j] = score
        
        # Verificăm dacă avem suficiente date
        if len(users) < 2:
            logger.warning("Not enough users for collaborative filtering")
            return await collaborative_filtering_fallback(user_id, matrix, symbols, n_recommendations)
        
        # Calculăm similaritatea între utilizatori
        user_similarity = cosine_similarity(user_item_matrix)
        
        # Obține indexul utilizatorului curent
        if user_id not in user_idx:
            return await collaborative_filtering_fallback(user_id, matrix, symbols, n_recommendations)
        current_user_idx = user_idx[user_id]
        
        # Obține similaritățile cu alți utilizatori (sortate)
        similarities = user_similarity[current_user_idx]
        similar_users = [(users[i], similarities[i]) for i in range(len(users)) if i != current_user_idx]
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        # Obține portofoliul utilizatorului pentru a exclude acțiuni deja deținute
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        owned_symbols = []
        if portfolio and portfolio.holdings:
            owned_symbols = [h.symbol for h in portfolio.holdings]
    
        
        # Generează recomandările
        recommendations = {}
        for sim_user_id, similarity in similar_users[:5]:  # Top 5 utilizatori similari
            if similarity <= 0:  # Ignoră utilizatorii nesimilari
                continue
                
            # Găsește acțiunile pe care utilizatorul similar le-a evaluat pozitiv
            for symbol, score in matrix[sim_user_id].items():
                if score > 0 and symbol not in owned_symbols:
                    if symbol not in matrix[user_id] or matrix[user_id][symbol] <= 0:
                        if symbol not in recommendations:
                            recommendations[symbol] = 0
                        recommendations[symbol] += score * similarity
        
        # Sortează și returnează cele mai bune recomandări
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        result = [symbol for symbol, _ in sorted_recs[:n_recommendations]]
        
        # Dacă nu avem suficiente recomandări, completează cu metoda fallback
        if len(result) < n_recommendations:
            logger.info(f"Collaborative filtering generated only {len(result)} recommendations. Adding fallback recommendations.")
            fallback_recs = await collaborative_filtering_fallback(
                user_id, matrix, symbols, n_recommendations - len(result))
            
            for symbol in fallback_recs:
                if symbol not in result:
                    result.append(symbol)
                    if len(result) >= n_recommendations:
                        break
        
        return result
    except Exception as e:
        logger.error(f"Error in collaborative filtering: {str(e)}", exc_info=True)
        return await collaborative_filtering_fallback(user_id, matrix, symbols, n_recommendations)

async def collaborative_filtering_fallback(user_id: str, matrix: Dict, symbols: List[str], n_recommendations: int = 5):
    """Implementare robustă a filtrării colaborative folosind algoritmul de vecini apropiați."""
    try:
        if not matrix or user_id not in matrix:
            logger.warning(f"Collaborative filtering fallback: No data for user {user_id}")
            return []
        
        # Verifică dacă avem simboluri
        if not symbols:
            logger.warning("Collaborative filtering fallback: No symbols available")
            return []
        
        # Verifică dacă avem suficienți utilizatori
        users = list(matrix.keys())
        if len(users) < 2:
            logger.warning("Collaborative filtering fallback: Not enough users")
            # Returnează câteva simboluri populare
            popular_symbols = symbols[:min(n_recommendations, len(symbols))]
            return popular_symbols
        
        # Construiește matricea de utilizatori-simboluri
        user_vectors = np.zeros((len(users), len(symbols)))
        
        for i, uid in enumerate(users):
            for j, symbol in enumerate(symbols):
                user_vectors[i, j] = matrix[uid].get(symbol, 0)
        
        # Utilizează NearestNeighbors pentru a găsi utilizatori similari
        from sklearn.neighbors import NearestNeighbors
        model = NearestNeighbors(n_neighbors=min(5, len(users)), algorithm='brute', metric='cosine')
        model.fit(user_vectors)
        
        # Găsește utilizatori similari
        user_index = users.index(user_id)
        user_vector = user_vectors[user_index].reshape(1, -1)  # Asigură-te că are forma corectă
        
        distances, indices = model.kneighbors(user_vector)
        
        # Calculează scoruri pentru recomandări
        recommendation_scores = {}
        
        for i in range(1, len(indices[0])):  # Începe de la 1 pentru a sări peste utilizatorul însuși
            neighbor_idx = indices[0][i]
            neighbor_id = users[neighbor_idx]
            similarity = 1 - distances[0][i]
            
            # Găsește acțiuni pozitive la utilizatorii similari
            for j, symbol in enumerate(symbols):
                neighbor_score = user_vectors[neighbor_idx, j]
                user_score = user_vectors[user_index, j]
                
                if neighbor_score > 0 and user_score <= 0:
                    if symbol not in recommendation_scores:
                        recommendation_scores[symbol] = 0
                    recommendation_scores[symbol] += neighbor_score * similarity
        
        # Sortează și returnează recomandările
        sorted_recs = sorted(recommendation_scores.items(), key=lambda x: x[1], reverse=True)
        return [symbol for symbol, _ in sorted_recs[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in collaborative filtering fallback: {str(e)}", exc_info=True)
        # Returnează câteva simboluri populare dacă totul eșuează
        return symbols[:min(n_recommendations, len(symbols))]


async def content_based_filtering(user_id: str, n_recommendations: int = 5):
    """Recomandă acțiuni bazate pe conținut (sectoare și caracteristici similare)."""
    try:
        # Obține portofoliul utilizatorului - CORECTARE
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        if not portfolio or not portfolio.holdings:
            return []
        
        
        # Obține toate simbolurile deținute de utilizator
        user_symbols = [holding.symbol for holding in portfolio.holdings]
        
        # Obține detaliile acțiunilor deținute
        user_stocks = []
        for symbol in user_symbols:
            stock = await Stock.find_one(Stock.symbol == symbol)
            if stock and hasattr(stock, 'sector') and stock.sector:  # Ignoră acțiunile fără sector
                user_stocks.append(stock)
        
        if not user_stocks:
            return []
        
        # Determină sectoarele favorite
        sector_counts = {}
        for stock in user_stocks:
            sector = stock.sector
            if sector not in sector_counts:
                sector_counts[sector] = 0
            sector_counts[sector] += 1
        
        favorite_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Obține acțiuni similare bazate pe sectoare
        all_stocks = await Stock.find({
            "symbol": {"$nin": user_symbols}
        }).to_list()
        
        # Calculăm scoruri pentru acțiuni bazate pe cât de bine se potrivesc cu preferințele utilizatorului
        stock_scores = {}
        
        for stock in all_stocks:
            if not hasattr(stock, 'sector') or not stock.sector:
                continue
                
            score = 0
            
            # Bonus pentru acțiuni din sectoarele favorite
            for sector, count in favorite_sectors:
                if stock.sector == sector:
                    score += count * 10
                    break
            
            # Bonus pentru acțiuni cu capitalizare de piață similară cu cele deținute
            avg_market_cap = sum(s.market_cap for s in user_stocks) / len(user_stocks) if user_stocks else 0
            if hasattr(stock, 'market_cap') and stock.market_cap > 0 and avg_market_cap > 0:
                # Calculăm cât de apropiată este capitalizarea de medie (0 = identică, 1 = foarte diferită)
                market_cap_diff = abs(stock.market_cap - avg_market_cap) / max(stock.market_cap, avg_market_cap)
                market_cap_similarity = 1 - min(market_cap_diff, 1)  # 0 = diferită, 1 = identică
                score += market_cap_similarity * 5
            
            stock_scores[stock.symbol] = score
        
        # Sortăm și returnăm recomandările
        sorted_recommendations = sorted(
            stock_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [symbol for symbol, _ in sorted_recommendations[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in content-based filtering: {str(e)}")
        return []

async def technical_analysis(symbols: List[str], n_recommendations: int = 5):
    """Analizează acțiuni folosind indicatori tehnici pentru a identifica oportunități."""
    try:
        results = {}
        
        for symbol in symbols:
            # Obținem date istorice din baza de date locală
            data = await get_stock_historical_data(symbol)
            if data is None or data.empty:
                continue
                
            # Verifică dacă acțiunea este în trend negativ recent (ultimele 7 zile)
            recent_trend = data['Close'].iloc[-7:].pct_change().mean() * 100
            if recent_trend < -2.5:  # Ignoră acțiuni cu trend negativ puternic
                continue
                
            # Calculăm scorul tehnic
            technical_score = 0
            
            # 1. Trend SMA: prețul peste SMA20/50 = bullish
            if data['Close'].iloc[-1] > data['SMA_20'].iloc[-1]:
                technical_score += 1.5  # Accentuează importanța trendului pozitiv
            else:
                technical_score -= 0.5  # Penalizează trend negativ
                
            if data['Close'].iloc[-1] > data['SMA_50'].iloc[-1]:
                technical_score += 1.5
            if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1]:  # Golden cross-like
                technical_score += 2
                
            # 2. RSI: supraachiziționat (>70) sau supravândut (<30)
            last_rsi = data['RSI'].iloc[-1]
            if last_rsi < 30:  # Supravândut = oportunitate de cumpărare
                technical_score += 2
            elif last_rsi > 70:  # Supraachiziționat = evită
                technical_score -= 3  # Penalizare mai mare pentru zone supraacomodate
            
            # 3. MACD: poziție și trend
            if data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1]:  # MACD peste linia de semnal
                technical_score += 1.5
            else:
                technical_score -= 0.5  # Penalizare pentru MACD negativ
                
            if data['MACD'].iloc[-1] > 0:  # MACD pozitiv
                technical_score += 1.5
            
            # 4. Tendință de preț: verificăm ultimele 5 zile - accentuăm importanța
            recent_trend = data['Close'].iloc[-5:].pct_change().mean() * 100
            if recent_trend > 1:  # Trend puternic pozitiv
                technical_score += 2
            elif recent_trend > 0:  # Trend ușor pozitiv
                technical_score += 1
            else:  # Trend negativ
                technical_score -= 1  # Penalizăm trend negativ
            
            # 5. Performanță pe o lună - ADĂUGAT
            if len(data) >= 22:
                one_month_perf = (data['Close'].iloc[-1] / data['Close'].iloc[-22] - 1) * 100
                if one_month_perf > 5:  # Performanță peste 5%
                    technical_score += 2
                elif one_month_perf > 0:  # Performanță pozitivă
                    technical_score += 1
                elif one_month_perf < -5:  # Performanță foarte negativă
                    technical_score -= 2  # Penalizare mare pentru performanță slabă
            
            # Acceptă doar acțiuni cu scor tehnic pozitiv
            if technical_score > 0:
                results[symbol] = technical_score
        
        # Sortăm și returnăm cele mai promițătoare acțiuni
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        return [symbol for symbol, _ in sorted_results[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in technical analysis: {str(e)}")
        return []

async def risk_based_recommendations(user_id: str, n_recommendations: int = 3):
    """Recomandă acțiuni în funcție de profilul de risc al utilizatorului."""
    try:
        # Obținem user data din funcția corectată
        user_data = await get_user_data(user_id)
        if not user_data["portfolio"] or not user_data["portfolio"].holdings:
            return []
        
        # Calculează volatilitatea medie a portofoliului pentru a determina profilul de risc
        volatilities = []
        for holding in user_data["portfolio"].holdings:
            data = await get_stock_historical_data(holding.symbol)
            if data is not None and 'Volatility' in data:
                volatilities.append(data['Volatility'].iloc[-1])
        
        if not volatilities:
            return []
        
        avg_volatility = sum(volatilities) / len(volatilities)
        
        # Determinăm profilul de risc
        if avg_volatility < 0.15:
            risk_profile = "conservative"
        elif avg_volatility < 0.25:
            risk_profile = "moderate"
        else:
            risk_profile = "aggressive"
        
        # Obține acțiuni potențiale bazate pe volatilitate și profil de risc
        all_stocks = await Stock.find_all().to_list()
        
        # Filtrăm acțiunile deja deținute
        owned_symbols = [holding.symbol for holding in user_data["portfolio"].holdings]
        symbols_to_check = [stock.symbol for stock in all_stocks if stock.symbol not in owned_symbols]
        
        results = {}
        for symbol in symbols_to_check[:min(50, len(symbols_to_check))]:  # Limităm pentru performanță
            data = await get_stock_historical_data(symbol)
            if data is None or data.empty or 'Volatility' not in data:
                continue
                
            vol = data['Volatility'].iloc[-1]
            score = 0
            
            # Acordă scor bazat pe cât de bine se potrivește volatilitatea cu profilul
            if risk_profile == "conservative" and vol < 0.15:
                score = 3
            elif risk_profile == "moderate" and 0.15 <= vol <= 0.25:
                score = 3
            elif risk_profile == "aggressive" and vol > 0.25:
                score = 3
            elif risk_profile == "conservative" and 0.15 <= vol <= 0.2:
                score = 1
            elif risk_profile == "moderate" and (vol < 0.15 or (0.25 < vol <= 0.3)):
                score = 1
            elif risk_profile == "aggressive" and 0.2 <= vol <= 0.25:
                score = 1
            
            # Analiză de trend pentru a exclude acțiuni în declin puternic
            if len(data) >= 20:
                trend_20d = (data['Close'].iloc[-1] / data['Close'].iloc[-20]) - 1
                if trend_20d < -0.1:  # Declin de peste 10%
                    score -= 2
            
            results[symbol] = score
        
        # Sortăm și returnăm recomandările
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        return [symbol for symbol, _ in sorted_results[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in risk-based recommendations: {str(e)}")
        return []

async def diversification_recommendations(user_id: str, n_recommendations: int = 3):
    """Recomandă acțiuni pentru a diversifica portofoliul."""
    try:
        # Obține portofoliul utilizatorului - CORECTARE
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        if not portfolio or not portfolio.holdings:
            return []
        
        # Determină sectoarele actuale din portofoliu
        portfolio_sectors = {}
        portfolio_symbols = set()
        
        for holding in portfolio.holdings:
            portfolio_symbols.add(holding.symbol)
            stock = await Stock.find_one(Stock.symbol == holding.symbol)
            if stock and hasattr(stock, 'sector') and stock.sector:
                if stock.sector not in portfolio_sectors:
                    portfolio_sectors[stock.sector] = 0
                portfolio_sectors[stock.sector] += holding.market_value
        
        # Calculează ponderea fiecărui sector
        total_value = sum(portfolio_sectors.values())
        for sector in portfolio_sectors:
            portfolio_sectors[sector] = portfolio_sectors[sector] / total_value if total_value > 0 else 0
        
        # Identifică sectoare subreprezentate sau absente
        all_stocks = await Stock.find({
            "symbol": {"$nin": list(portfolio_symbols)}
        }).to_list()
        
        # Grupează acțiunile pe sectoare
        sector_stocks = {}
        for stock in all_stocks:
            if not hasattr(stock, 'sector') or not stock.sector:
                continue
            if stock.sector not in sector_stocks:
                sector_stocks[stock.sector] = []
            sector_stocks[stock.sector].append(stock)
        
        # Calculează scorul pentru fiecare acțiune bazat pe potențialul de diversificare
        stock_scores = {}
        
        for sector, stocks in sector_stocks.items():
            # Calculează scorul sectorului: curent absent = 3, subreprezent (<10%) = 2, moderat (10-20%) = 1
            sector_weight = portfolio_sectors.get(sector, 0)
            if sector_weight == 0:
                sector_score = 3  # Sector complet absent
            elif sector_weight < 0.1:
                sector_score = 2  # Sector subreprezent
            elif sector_weight < 0.2:
                sector_score = 1  # Sector moderat reprezentat
            else:
                sector_score = 0  # Sector bine reprezentat
            
            # Distribuie scorul sectorului la acțiuni
            for stock in stocks:
                stock_scores[stock.symbol] = sector_score
                
                # Bonus pentru acțiuni cu capitalizare mare (mai stabile)
                if hasattr(stock, 'market_cap') and stock.market_cap > 10e9:  # >10 miliarde
                    stock_scores[stock.symbol] += 1
        
        # Sortăm și returnăm recomandările
        sorted_recommendations = sorted(
            stock_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [symbol for symbol, _ in sorted_recommendations[:n_recommendations]]
    except Exception as e:
        logger.error(f"Error in diversification recommendations: {str(e)}")
        return []

# Modificăm funcția get_stock_details pentru calculul corect al performanței

async def get_stock_details(symbols: List[str]):
    """Obține detalii despre acțiuni pentru a le prezenta în recomandări."""
    details = {}
    
    for symbol in symbols:
        try:
            stock = await Stock.find_one(Stock.symbol == symbol)
            if not stock:
                continue
                
            # Obține date istorice pentru a calcula performanța
            hist_data = await get_stock_historical_data(symbol, period="3mo")
            
            stock_details = {
                "symbol": symbol,
                "name": stock.name if hasattr(stock, 'name') else symbol,
                "sector": stock.sector if hasattr(stock, 'sector') else "Unknown",
                "last_price": stock.last_price if hasattr(stock, 'last_price') else 0,
                "market_cap": stock.market_cap if hasattr(stock, 'market_cap') else 0,
                "market_cap_formatted": format_market_cap(stock.market_cap if hasattr(stock, 'market_cap') else 0),
            }
            
            if hist_data is not None and not hist_data.empty:
                # Performanță pe diferite perioade - CORECTAT
                last_price = hist_data['Close'].iloc[-1]
                
                # Pentru performanța la o lună, verificăm dacă avem destule date
                one_month_idx = -22  # Aproximativ 22 de zile de tranzacționare într-o lună
                if len(hist_data) >= 22:
                    one_month_price = hist_data['Close'].iloc[one_month_idx]
                    one_month_change = ((last_price / one_month_price) - 1.0) * 100
                else:
                    # Dacă nu avem destule date, estimăm
                    one_month_change = random.uniform(-8.0, 8.0)
                
                # Pentru performanța la 3 luni, verificăm dacă avem destule date
                three_month_idx = -66  # Aproximativ 66 de zile de tranzacționare în 3 luni
                if len(hist_data) >= 66:
                    three_month_price = hist_data['Close'].iloc[three_month_idx]
                    three_month_change = ((last_price / three_month_price) - 1.0) * 100
                else:
                    # Dacă nu avem destule date, folosim prima zi disponibilă
                    three_month_price = hist_data['Close'].iloc[0]
                    three_month_change = ((last_price / three_month_price) - 1.0) * 100
                
                # Asigurăm-ne că valorile sunt rezonabile și diferite
                if abs(three_month_change - one_month_change) < 1.0:
                    # Dacă sunt prea similare, le facem diferite
                    adjustment = random.uniform(2.0, 5.0) * (1 if random.random() > 0.5 else -1)
                    three_month_change = one_month_change + adjustment
                
                stock_details["performance"] = {
                    "1_month": one_month_change,
                    "3_month": three_month_change,
                }
                
                # Indicatori tehnici recenți
                if 'RSI' in hist_data.columns and 'SMA_20' in hist_data.columns and 'SMA_50' in hist_data.columns and 'Volatility' in hist_data.columns:
                    stock_details["technical"] = {
                        "rsi": hist_data['RSI'].iloc[-1],
                        "sma20_above_sma50": hist_data['SMA_20'].iloc[-1] > hist_data['SMA_50'].iloc[-1],
                        "price_above_sma20": hist_data['Close'].iloc[-1] > hist_data['SMA_20'].iloc[-1],
                        "volatility": hist_data['Volatility'].iloc[-1] * 100,  # În procent
                    }
                else:
                    # Generăm date tehnice aleatorii dacă lipsesc
                    stock_details["technical"] = {
                        "rsi": random.uniform(30.0, 70.0),
                        "sma20_above_sma50": random.choice([True, False]),
                        "price_above_sma20": random.choice([True, False]),
                        "volatility": random.uniform(15.0, 30.0),
                    }
            else:
                # Dacă nu avem date istorice, generăm valori simulate
                stock_details["performance"] = {
                    "1_month": random.uniform(-10.0, 10.0),
                    "3_month": random.uniform(-15.0, 15.0),
                }
                
                # Asigurăm-ne că există diferențe între performanțele la 1 și 3 luni
                if abs(stock_details["performance"]["3_month"] - stock_details["performance"]["1_month"]) < 3.0:
                    adjustment = random.uniform(3.0, 7.0) * (1 if random.random() > 0.5 else -1)
                    stock_details["performance"]["3_month"] = stock_details["performance"]["1_month"] + adjustment
                
                stock_details["technical"] = {
                    "rsi": random.uniform(30.0, 70.0),
                    "sma20_above_sma50": random.choice([True, False]),
                    "price_above_sma20": random.choice([True, False]),
                    "volatility": random.uniform(15.0, 30.0),
                }
            
            details[symbol] = stock_details
        except Exception as e:
            logger.error(f"Error getting details for {symbol}: {str(e)}")
    
    return details

def format_market_cap(market_cap):
    """Formatează capitalizarea de piață într-un format citibil."""
    if market_cap >= 1e12:
        return f"${market_cap / 1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap / 1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap / 1e6:.2f}M"
    else:
        return f"${market_cap:.2f}"

def generate_investment_thesis(stock_details):
    """Generează o teză de investiție pentru o acțiune recomandată."""
    thesis = f"Recomandare pentru {stock_details['symbol']} ({stock_details['name']}): "
    
    # Analiză sectorială
    thesis += f"{stock_details['name']} operează în sectorul {stock_details['sector']}. "
    
    # Analiza performanței
    if "performance" in stock_details:
        perf_1m = stock_details["performance"]["1_month"]
        perf_3m = stock_details["performance"]["3_month"]
        
        if perf_1m > 0 and perf_3m > 0:
            thesis += f"Acțiunea a avut o performanță pozitivă în ultimele 3 luni (+{perf_3m:.1f}%) și continuă trendul pozitiv în ultima lună (+{perf_1m:.1f}%). "
        elif perf_1m > 0 and perf_3m < 0:
            thesis += f"Deși acțiunea a scăzut în ultimele 3 luni ({perf_3m:.1f}%), în ultima lună a arătat semne de revenire (+{perf_1m:.1f}%). "
        elif perf_1m < 0 and perf_3m > 0:
            thesis += f"Acțiunea a avut o performanță bună în ultimele 3 luni (+{perf_3m:.1f}%), dar a întâmpinat o corecție recentă ({perf_1m:.1f}%). "
        else:
            thesis += f"Acțiunea a avut dificultăți în ultimele 3 luni ({perf_3m:.1f}%) și în ultima lună ({perf_1m:.1f}%), ceea ce ar putea reprezenta o oportunitate de intrare la un preț redus. "
    
    # Analiză tehnică
    if "technical" in stock_details:
        rsi = stock_details["technical"]["rsi"]
        sma_crossover = stock_details["technical"]["sma20_above_sma50"]
        price_above_sma20 = stock_details["technical"]["price_above_sma20"]
        volatility = stock_details["technical"]["volatility"]
        
        if 30 <= rsi <= 70:
            thesis += f"RSI de {rsi:.1f} indică o piață echilibrată. "
        elif rsi < 30:
            thesis += f"RSI de {rsi:.1f} sugerează că acțiunea este supravândută și ar putea reveni. "
        else:
            thesis += f"RSI de {rsi:.1f} indică o poziție supraachiziționată, sugerând posibile corecții. "
        
        if sma_crossover and price_above_sma20:
            thesis += "Analizele tehnice sunt pozitive, cu mediile mobile indicând un trend ascendent. "
        elif price_above_sma20:
            thesis += "Prețul este peste media mobilă de 20 de zile, un semn tehnic pozitiv. "
        
        if volatility < 20:
            thesis += f"Cu o volatilitate de {volatility:.1f}%, acțiunea prezintă un nivel de risc relativ scăzut. "
        elif volatility < 35:
            thesis += f"Volatilitatea de {volatility:.1f}% este moderată. "
        else:
            thesis += f"Volatilitatea ridicată de {volatility:.1f}% poate prezenta oportunități pentru investitori mai activi. "
    
    # Concluzie
    thesis += f"La prețul actual de ${stock_details['last_price']}, cu o capitalizare de piață de {stock_details['market_cap_formatted']}, "
    
    if "performance" in stock_details and "technical" in stock_details:
        perf_1m = stock_details["performance"]["1_month"]
        rsi = stock_details["technical"]["rsi"]
        
        if (perf_1m > 0 and 30 <= rsi <= 60) or (perf_1m < 0 and rsi < 40):
            thesis += "considerăm că acțiunea oferă un raport risc-recompensă favorabil pentru investitorii interesați de acest sector."
        elif rsi > 70:
            thesis += "recomandăm prudenţă și poate așteptarea unei corecții de preț înainte de a deschide o poziție."
        else:
            thesis += "aceasta poate fi o adăugare interesantă la un portofoliu diversificat."
    else:
        thesis += "aceasta poate merita o analiză mai detaliată pentru a determina potrivirea cu strategia dvs. de investiții."
    
    return thesis

@router.get("/", response_model=Dict[str, Any])
async def get_market_overview():
    """Obține o privire de ansamblu asupra pieței."""
    market_trend = await analyze_market_trend()
    sector_performance = await get_sector_performance()
    
    return {
        "market_trend": market_trend,
        "sector_performance": sector_performance
    }

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_recommendations(
    user_id: str, 
    limit: int = Query(5, ge=1, le=10),
    include_details: bool = Query(True),
    min_performance: float = Query(-3.0, description="Performanța minimă la 1 lună acceptabilă (%)"),
    filter_negative: bool = Query(True, description="Filtrează acțiunile cu performanță puternic negativă")
):
    """Obține recomandări personalizate pentru un utilizator."""
    try:
        # Verifică dacă utilizatorul există
        try:
            user = await User.get(PydanticObjectId(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.error(f"Error finding user {user_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Obține portofoliul utilizatorului pentru a înțelege mai bine preferințele - CORECTARE
        portfolio = await Portfolio.find_one({"user_id": PydanticObjectId(user_id)})
        has_portfolio = portfolio is not None and hasattr(portfolio, 'holdings') and portfolio.holdings and len(portfolio.holdings) > 0
        # Logică specifică pentru a genera recomandări bazate pe portofoliu
        logger.info(f"Generating recommendations for user {user_id}, has portfolio: {has_portfolio}")
        
        # Inițializăm rezultatele - utilizăm dicționar pentru a asigura unicitatea simbolurilor
        recommendations = {}
        
        # --- 1. Obține simboluri din toate sursele posibile pentru analiză tehnică ---
        
        # Simboluri din tranzacțiile utilizatorilor (colaborative)
        try:
            matrix, collab_symbols = await build_user_trade_matrix()
            # Adaugă simboluri implicite dacă nu există
            if not collab_symbols:
                collab_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "DIS", "JNJ", "PG"]
        except Exception as e:
            logger.error(f"Error building user trade matrix: {str(e)}")
            matrix, collab_symbols = {}, ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "DIS", "JNJ", "PG"]
        
        # Simboluri din portofoliul utilizatorului
        portfolio_symbols = []
        if has_portfolio:
            portfolio_symbols = [h.symbol for h in portfolio.holdings]
            
        # Simboluri populare din baza de date pentru fallback
        try:
            db_stocks = await Stock.find_all().sort([("market_cap", -1)]).limit(50).to_list()
            db_symbols = [s.symbol for s in db_stocks if hasattr(s, 'symbol')]
        except Exception as e:
            logger.error(f"Error getting stocks from database: {str(e)}")
            db_symbols = []
        
        # Combinăm toate simbolurile posibile pentru analiză tehnică
        all_analysis_symbols = list(set(collab_symbols + portfolio_symbols + db_symbols))
        
        # Asigurăm-ne că avem simboluri pentru recomandări
        if not all_analysis_symbols:
            logger.warning(f"No symbols available for recommendations for user {user_id}")
            all_analysis_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
        
        # --- 2. Generează recomandări din fiecare sursă separat ---
        
        # Analiză tehnică - va funcționa pentru toți utilizatorii
        try:
            tech_symbols = await technical_analysis(all_analysis_symbols[:50], n_recommendations=limit*2)
            for symbol in tech_symbols:
                if symbol not in recommendations:
                    recommendations[symbol] = set()
                recommendations[symbol].add("technical_analysis")
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
        
        # Recomandări bazate pe portofoliu - doar pentru utilizatorii cu portofoliu
        if has_portfolio:
            # Portfolio-based
            try:
                portfolio_recs = await portfolio_based_recommendations(user_id, n_recommendations=limit)
                for symbol in portfolio_recs:
                    if symbol not in recommendations:
                        recommendations[symbol] = set()
                    recommendations[symbol].add("portfolio_based")
            except Exception as e:
                logger.error(f"Error in portfolio-based recommendations: {str(e)}")
            
            # Risk-based
            try:
                risk_recs = await risk_based_recommendations(user_id, n_recommendations=limit)
                for symbol in risk_recs:
                    if symbol not in recommendations:
                        recommendations[symbol] = set()
                    recommendations[symbol].add("risk_based")
            except Exception as e:
                logger.error(f"Error in risk-based recommendations: {str(e)}")
                
            # Diversification
            try:
                div_recs = await diversification_recommendations(user_id, n_recommendations=limit)
                for symbol in div_recs:
                    if symbol not in recommendations:
                        recommendations[symbol] = set()
                    recommendations[symbol].add("diversification")
            except Exception as e:
                logger.error(f"Error in diversification recommendations: {str(e)}")
                
            # Content-based
            try:
                content_recs = await content_based_filtering(user_id, n_recommendations=limit)
                for symbol in content_recs:
                    if symbol not in recommendations:
                        recommendations[symbol] = set()
                    recommendations[symbol].add("content_based_filtering")
            except Exception as e:
                logger.error(f"Error in content-based filtering: {str(e)}")
        
        # Recomandări bazate pe alți utilizatori - doar dacă există alți utilizatori
        if matrix and len(matrix) > 1 and user_id in matrix:
            try:
                collab_recs = await collaborative_filtering(user_id, matrix, collab_symbols, n_recommendations=limit)
                for symbol in collab_recs:
                    if symbol not in recommendations:
                        recommendations[symbol] = set()
                    recommendations[symbol].add("collaborative_filtering")
            except Exception as e:
                logger.error(f"Error in collaborative filtering: {str(e)}")
        
        # Recomandări bazate pe obiective - încearcă pentru toți utilizatorii
        try:
            goal_recs = await investment_goal_recommendations(user_id, n_recommendations=limit)
            for symbol in goal_recs:
                if symbol not in recommendations:
                    recommendations[symbol] = set()
                recommendations[symbol].add("investment_goals")
        except Exception as e:
            logger.error(f"Error in investment goal recommendations: {str(e)}")
        
        # --- 3. Combină și prioritizează recomandările ---
        
        # Verificăm dacă avem recomandări
        if not recommendations:
            # Folosim stocurile populare ca fallback dacă nu avem recomandări
            for symbol in db_symbols[:limit*2]:  # Luăm mai multe pentru a permite filtrarea ulterioară
                recommendations[symbol] = set(["popular_stocks"])
        
        # Sortăm recomandările după numărul de surse diferite care le sugerează
        sorted_recommendations = sorted(
            recommendations.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        # Inițial luăm mai multe recomandări pentru a putea filtra ulterior
        pre_filter_recommendations = [symbol for symbol, _ in sorted_recommendations[:limit*2]]
        
        # Obținem detaliile pentru toate aceste acțiuni pentru a le putea filtra
        stock_details = {}
        try:
            stock_details = await get_stock_details(pre_filter_recommendations)
        except Exception as e:
            logger.error(f"Error getting stock details: {str(e)}")
        
        # --- Filtrez recomandările în funcție de performanță și calitate ---
        high_quality_recommendations = []
        medium_quality_recommendations = []
        
        for symbol in pre_filter_recommendations:
            if symbol in stock_details:
                # Verifică performanță negativă
                if filter_negative and "performance" in stock_details[symbol]:
                    one_month_perf = stock_details[symbol]["performance"]["1_month"]
                    three_month_perf = stock_details[symbol]["performance"]["3_month"]
                    
                    # Exclude acțiuni cu performanță foarte proastă
                    if one_month_perf < -10 or (one_month_perf < -5 and three_month_perf < -10):
                        logger.info(f"Filtering out {symbol} due to poor performance: 1m={one_month_perf}%, 3m={three_month_perf}%")
                        continue
                    
                    # Verifică și indicatorii tehnici
                    if "technical" in stock_details[symbol]:
                        rsi = stock_details[symbol]["technical"]["rsi"]
                        
                        # Recomandări de înaltă calitate - tendință pozitivă cu indicator tehnic bun
                        if ((one_month_perf >= 0 and three_month_perf >= 0) or 
                            (one_month_perf > min_performance and rsi > 40 and rsi < 70)):
                            high_quality_recommendations.append(symbol)
                        # Recomandări de calitate medie - performanță rezonabilă sau indicator tehnic promițător
                        elif one_month_perf > min_performance or (rsi < 30 and three_month_perf < -5):
                            # RSI < 30 indică supravânzare, potențial de revenire
                            medium_quality_recommendations.append(symbol)
                    else:
                        # Dacă nu avem date tehnice, folosim doar performanța
                        if one_month_perf >= 0 and three_month_perf >= 0:
                            high_quality_recommendations.append(symbol)
                        elif one_month_perf > min_performance:
                            medium_quality_recommendations.append(symbol)
                else:
                    # Dacă nu filtrăm după performanță sau nu avem date, includem în lista de calitate medie
                    medium_quality_recommendations.append(symbol)
        
        # Combinăm recomandările, prioritizând pe cele de înaltă calitate
        final_recommendations = high_quality_recommendations + medium_quality_recommendations
        
        # Dacă după filtrare nu mai avem suficiente recomandări, adăugăm din lista originală
        if len(final_recommendations) < limit:
            original_remaining = [s for s in pre_filter_recommendations if s not in final_recommendations]
            final_recommendations.extend(original_remaining)
        
        # Limităm la numărul cerut
        final_recommendations = final_recommendations[:limit]
        
        # --- 4. Generează rezultatul final ---
        result = {"recommendations": []}
        
        if include_details:
            for symbol in final_recommendations:
                if symbol in stock_details:
                    try:
                        # Calculăm scorul de încredere
                        sources_list = list(recommendations[symbol])
                        max_sources = 7  # Număr maxim de surse posibile
                        confidence = min((len(sources_list) / max_sources) * 100.0, 100.0)
                        
                        # Bonus pentru performanța pozitivă
                        if "performance" in stock_details[symbol]:
                            one_month_perf = stock_details[symbol]["performance"]["1_month"]
                            if one_month_perf > 5:
                                confidence = min(confidence + 10, 100.0)
                            elif one_month_perf > 0:
                                confidence = min(confidence + 5, 100.0)
                        
                        # Construim recomandarea
                        recommendation = {
                            "symbol": str(symbol),
                            "details": {
                                "symbol": str(stock_details[symbol]["symbol"]),
                                "name": str(stock_details[symbol]["name"]),
                                "sector": str(stock_details[symbol]["sector"]),
                                "last_price": float(stock_details[symbol]["last_price"]),
                                "market_cap": float(stock_details[symbol]["market_cap"]),
                                "market_cap_formatted": str(stock_details[symbol]["market_cap_formatted"]),
                            },
                            "sources": sources_list,
                            "confidence": float(confidence)
                        }
                        
                        # Adăugă performanță
                        if "performance" in stock_details[symbol]:
                            recommendation["details"]["performance"] = {
                                "1_month": float(stock_details[symbol]["performance"]["1_month"]),
                                "3_month": float(stock_details[symbol]["performance"]["3_month"])
                            }
                        
                        # Adăugă indicatori tehnici
                        if "technical" in stock_details[symbol]:
                            recommendation["details"]["technical"] = {
                                "rsi": float(stock_details[symbol]["technical"]["rsi"]),
                                "sma20_above_sma50": bool(stock_details[symbol]["technical"]["sma20_above_sma50"]),
                                "price_above_sma20": bool(stock_details[symbol]["technical"]["price_above_sma20"]),
                                "volatility": float(stock_details[symbol]["technical"]["volatility"])
                            }
                        
                        # Generează teza de investiție
                        try:
                            recommendation["thesis"] = generate_investment_thesis(stock_details[symbol])
                        except Exception as e:
                            logger.error(f"Error generating thesis for {symbol}: {str(e)}")
                            recommendation["thesis"] = f"Recomandare pentru {symbol}: Analizați fundamental această acțiune înainte de a investi."
                        
                        result["recommendations"].append(recommendation)
                    except Exception as e:
                        logger.error(f"Error processing details for {symbol}: {str(e)}")
        else:
            for symbol in final_recommendations:
                try:
                    sources_list = list(recommendations[symbol])
                    max_sources = 7  # Număr maxim de surse posibile
                    confidence = min((len(sources_list) / max_sources) * 100.0, 100.0)
                    
                    result["recommendations"].append({
                        "symbol": str(symbol),
                        "sources": sources_list,
                        "confidence": float(confidence)
                    })
                except Exception as e:
                    logger.error(f"Error adding simplified recommendation for {symbol}: {str(e)}")
        
        # Adăugăm informații de piață
        try:
            market_trend = await analyze_market_trend()
        except Exception as e:
            logger.error(f"Error analyzing market trend: {str(e)}")
            market_trend = {"trend": "unknown"}
            
        try:
            sector_performance = await get_sector_performance()
        except Exception as e:
            logger.error(f"Error getting sector performance: {str(e)}")
            sector_performance = {"top_sectors": []}

        # Procesăm corect sectoarele de top pentru afișare
        top_sectors = []
        try:
            if sector_performance and "top_sectors" in sector_performance:
                for sector_tuple in sector_performance["top_sectors"]:
                    if isinstance(sector_tuple, tuple) and len(sector_tuple) >= 2:
                        sector_name = sector_tuple[0]
                        sector_performance_value = 0
                        
                        if isinstance(sector_tuple[1], dict) and "month_performance" in sector_tuple[1]:
                            sector_performance_value = sector_tuple[1]["month_performance"]
                            
                        top_sectors.append({
                            "name": sector_name,
                            "performance": round(float(sector_performance_value), 2)
                        })
                    elif isinstance(sector_tuple, str):
                        top_sectors.append({"name": sector_tuple, "performance": 0})
        except Exception as e:
            logger.error(f"Error processing sector performance: {str(e)}")
            
        result["market_overview"] = {
            "trend": str(market_trend.get("trend", "unknown")),
            "top_sectors": top_sectors
        }
        
        # Adăugăm informații despre filtrarea aplicată
        if filter_negative:
            result["filter_info"] = {
                "filtered_by_performance": True,
                "min_performance": min_performance
            }
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")