from fastapi import APIRouter, HTTPException, Request
import yfinance as yf
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import traceback
import sys
import json
import time
from datetime import datetime

router = APIRouter()

print("News router module loaded!")  # Debug la încărcarea modulului

class NewsItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    link: Optional[str] = None
    providerPublishTime: Optional[int] = None
    type: Optional[str] = None
    relatedTickers: Optional[List[str]] = None
    thumbnail: Optional[dict] = None
    
    # Permite câmpuri extra pentru a nu arunca erori la câmpuri necunoscute
    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

@router.get("/", response_model=List[NewsItem])
async def get_financial_news():
    """
    Get general financial news
    """
    print("GET /news endpoint called")

    # Folosim o listă mai lungă de tickeri pentru a mări șansele de a găsi știri
    tickers_to_try = [
        "AAPL", "MSFT", "GOOG", "AMZN", "SPY", "QQQ", "TSLA", "META", "NVDA", "JPM",
        "GE", "BAC", "F", "AMD", "INTC", "WFC", "PFE", "DIS", "XOM", "WMT",
        "^GSPC", "^DJI", "^IXIC"  # Adăugăm și indici pentru știri generale de piață
    ]

    all_news = []

    # Încercăm fiecare ticker până găsim știri
    for ticker in tickers_to_try:
        try:
            print(f"Fetching news for {ticker}")
            stock = yf.Ticker(ticker)
            
            # Verificăm explicit dacă obiectul are atributul news și dacă conține items
            if hasattr(stock, "news") and stock.news and len(stock.news) > 0:
                news_items = stock.news
                print(f"Found {len(news_items)} news items for {ticker}")
                all_news.extend(news_items)
                
                # Dacă am găsit destule știri, ne oprim
                if len(all_news) >= 30:
                    print(f"Reached sufficient news items: {len(all_news)}")
                    break
        except Exception as e:
            # Log eroarea dar continuăm cu următorul ticker
            print(f"Error fetching news for {ticker}: {str(e)}")
            print(f"Type of exception: {type(e).__name__}")
            continue

    # Dacă nu am găsit nicio știre, returnăm o listă goală
    if not all_news:
        print("No news found from any ticker.")
        return []

    # Eliminăm duplicatele folosind ID-urile
    seen_ids = set()
    unique_news = []

    for item in all_news:
        # Verificăm dacă item-ul e un dicționar valid
        if not isinstance(item, dict):
            print(f"Skipping non-dict news item: {type(item)}")
            continue
            
        # Extragem sau generăm ID-ul
        item_id = item.get("id")
        
        # Adăugăm știrea dacă ID-ul e unic
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_news.append(item)
        # Sau generăm un ID nou dacă nu există
        elif not item_id:
            generated_id = f"gen-{len(seen_ids)}"
            item["id"] = generated_id
            seen_ids.add(generated_id)
            unique_news.append(item)

    print(f"Found {len(unique_news)} unique news items")

    # Procesăm și returnăm știrile (maxim 20)
    processed_news = process_yfinance_news(unique_news[:20])

    # Verificăm dacă procesarea a returnat rezultate
    if not processed_news:
        print("No processed news after filtering.")
        return []

    print(f"Returning {len(processed_news)} news items")
    return processed_news


@router.get("/all", response_model=List[NewsItem])
async def get_all_financial_news():
    """
    Endpoint alternativ pentru știrile generale de piață
    """
    print("GET /news/all endpoint called")

    # Începem cu indici de piață pentru știri mai generale
    tickers_to_try = [
        "^GSPC", "^DJI", "^IXIC",  # Indici pentru știri generale
        "SPY", "QQQ", "DIA",       # ETF-uri pentru indici
        "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA", "JPM",
        "GE", "BAC", "F", "AMD", "INTC", "WFC", "PFE", "DIS", "XOM", "WMT"
    ]

    all_news = []

    # Încercăm fiecare ticker până găsim știri
    for ticker in tickers_to_try:
        try:
            print(f"Fetching news for {ticker}")
            stock = yf.Ticker(ticker)
            
            # Verificăm explicit dacă obiectul are atributul news și dacă conține items
            if hasattr(stock, "news") and stock.news and len(stock.news) > 0:
                news_items = stock.news
                print(f"Found {len(news_items)} news items for {ticker}")
                all_news.extend(news_items)
                
                # Dacă am găsit destule știri, ne oprim
                if len(all_news) >= 30:
                    print(f"Reached sufficient news items: {len(all_news)}")
                    break
        except Exception as e:
            # Log eroarea dar continuăm cu următorul ticker
            print(f"Error fetching news for {ticker}: {str(e)}")
            print(f"Type of exception: {type(e).__name__}")
            continue

    # Dacă nu am găsit nicio știre, returnăm o listă goală
    if not all_news:
        print("No news found from any ticker.")
        return []

    # Eliminăm duplicatele folosind ID-urile
    seen_ids = set()
    unique_news = []

    for item in all_news:
        # Verificăm dacă item-ul e un dicționar valid
        if not isinstance(item, dict):
            print(f"Skipping non-dict news item: {type(item)}")
            continue
            
        # Extragem sau generăm ID-ul
        item_id = item.get("id")
        
        # Adăugăm știrea dacă ID-ul e unic
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_news.append(item)
        # Sau generăm un ID nou dacă nu există
        elif not item_id:
            generated_id = f"gen-{len(seen_ids)}"
            item["id"] = generated_id
            seen_ids.add(generated_id)
            unique_news.append(item)

    print(f"Found {len(unique_news)} unique news items")

    # Procesăm și returnăm știrile (maxim 20)
    processed_news = process_yfinance_news(unique_news[:20])
    
    print(f"Returning {len(processed_news)} processed news items")
    return processed_news

@router.get("/by-ticker/{ticker}")
async def get_ticker_news(ticker: str):
    """
    Get news specific to a ticker symbol
    """
    print(f"GET /by-ticker/{ticker} endpoint called")
    
    try:
        print(f"Creating yf.Ticker object for {ticker}")
        stock = yf.Ticker(ticker)
        
        has_news = hasattr(stock, 'news')
        print(f"Ticker {ticker} has news attribute: {has_news}")
        
        if has_news and stock.news:
            news_items = stock.news
            print(f"Found {len(news_items)} news items for {ticker}")
            
            # Verificăm și printăm structura primului element pentru debugging
            if news_items and len(news_items) > 0:
                print(f"First news item keys: {list(news_items[0].keys())}")
                if 'content' in news_items[0]:
                    print(f"Content keys: {list(news_items[0]['content'].keys()) if isinstance(news_items[0]['content'], dict) else 'Content is not a dict'}")
            
            # Procesăm și returnăm știrile
            return process_yfinance_news(news_items)
        else:
            print(f"No news found for ticker {ticker}")
            return []
    except Exception as e:
        print(f"Error fetching news for ticker {ticker}: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        return []

def process_yfinance_news(raw_news):
    """
    Process news from yfinance to match our frontend expected format
    """
    print(f"Processing {len(raw_news)} news items")
    processed_news = []
    current_timestamp = int(time.time())
    
    for i, item in enumerate(raw_news[:20]):
        try:
            # Verificăm structura item-ului
            if not isinstance(item, dict):
                print(f"Item {i} is not a dictionary, skipping")
                continue
                
            # Extragem content din item
            content = {}
            if 'content' in item and isinstance(item['content'], dict):
                content = item['content']
            
            # Generăm id unic dacă nu există
            news_id = item.get('id') or content.get('id') or f"news-{current_timestamp}-{i}"
            
            # Determinăm titlul
            title = None
            if 'title' in content:
                title = content['title']
            elif 'title' in item:
                title = item['title']
            else:
                title = f"Financial News Update {i+1}"
            
            # Determinăm publisher
            publisher = "Financial News"
            if 'provider' in content and isinstance(content['provider'], dict):
                if 'displayName' in content['provider']:
                    publisher = content['provider']['displayName']
            elif 'publisher' in item:
                publisher = item['publisher']
            
            # Determinăm link
            link = None
            if 'clickThroughUrl' in content and isinstance(content['clickThroughUrl'], dict):
                if 'url' in content['clickThroughUrl']:
                    link = content['clickThroughUrl']['url']
            elif 'link' in item:
                link = item['link']
            
            # Determinăm timestamp de publicare
            pub_date = current_timestamp
            if 'pubDate' in content:
                pub_date_raw = content.get('pubDate')
                # Convertește string ISO în timestamp dacă e nevoie
                if isinstance(pub_date_raw, str):
                    try:
                        # Încercăm să convertim data ISO în timestamp
                        dt = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00'))
                        pub_date = int(dt.timestamp())
                    except Exception as e:
                        print(f"Couldn't parse date {pub_date_raw}: {str(e)}")
                        pub_date = current_timestamp
                else:
                    pub_date = pub_date_raw
            elif 'providerPublishTime' in item:
                pub_date_raw = item.get('providerPublishTime')
                # Verifică dacă trebuie să convertim din string
                if isinstance(pub_date_raw, str):
                    try:
                        # Încercăm să convertim data ISO în timestamp
                        dt = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00'))
                        pub_date = int(dt.timestamp())
                    except Exception as e:
                        print(f"Couldn't parse date {pub_date_raw}: {str(e)}")
                        pub_date = current_timestamp
                else:
                    pub_date = pub_date_raw
            
            # Determinăm tipul știrii
            news_type = "STORY"
            if 'contentType' in content:
                news_type = content['contentType']
            elif 'type' in item:
                news_type = item['type']
            
            # Determinăm ticker-ele asociate
            related_tickers = []
            if 'finance' in content and isinstance(content['finance'], dict):
                if 'stockTickers' in content['finance'] and isinstance(content['finance']['stockTickers'], list):
                    related_tickers = content['finance']['stockTickers']
            elif 'relatedTickers' in item and isinstance(item['relatedTickers'], list):
                related_tickers = item['relatedTickers']
            
            # Construim obiectul de știri
            news_item = {
                "id": news_id,
                "title": title,
                "publisher": publisher,
                "link": link,
                "providerPublishTime": pub_date,  # Acum ar trebui să fie întotdeauna un int
                "type": news_type,
                "relatedTickers": related_tickers
            }
            
            # Procesăm thumbnail
            if 'thumbnail' in item and isinstance(item['thumbnail'], dict):
                news_item["thumbnail"] = item["thumbnail"]
            elif 'images' in content and isinstance(content['images'], list) and content['images']:
                resolutions = []
                for img in content['images']:
                    if isinstance(img, dict) and 'url' in img:
                        resolutions.append({
                            "url": img["url"],
                            "width": img.get("width", 800),
                            "height": img.get("height", 600)
                        })
                
                if resolutions:
                    news_item["thumbnail"] = {
                        "resolutions": resolutions
                    }
            
            # Adăugăm știrea în lista procesată
            processed_news.append(news_item)
            print(f"Processed news item {i+1}: {news_item['title'][:30]}...")
            
        except Exception as e:
            print(f"Error processing news item {i}: {str(e)}")
            print(traceback.format_exc())
            continue
    
    print(f"Returning {len(processed_news)} processed news items")
    return processed_news

@router.get("/test")
async def test_news_endpoint():
    """Test endpoint to check if the news router is working"""
    print("GET /test endpoint called")
    return {"status": "ok", "message": "News API is working"}