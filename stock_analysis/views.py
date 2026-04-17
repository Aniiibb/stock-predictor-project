"""
Main views file for handling API endpoints and requests
This is where I handle all the API stuff, user management, and stock data
"""

from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .models import Stock, WatchlistItem
from django.db import models
from alpha_vantage.timeseries import TimeSeries
import random
from django.contrib.auth.decorators import login_required
from .ml_model import get_stock_prediction
import jwt
import datetime
from datetime import datetime, timedelta
from django.conf import settings
import time
from django.core.cache import cache
from requests.exceptions import RequestException

def get_company_news(symbol):
    """
    Gets news articles for a stock symbol from the last week
    Added some filters to get more relevant market-related news
    
    Args:
        symbol: The stock symbol to search for (like AAPL, MSFT etc)
        
    Returns:
        List of news articles with titles and stuff
    """
    api_key = os.getenv('NEWS_API_KEY')
    print(f"Using NewsAPI key: {api_key}")
    
    if not api_key:
        print("No API key found, returning sample data")
        return [
            {
                'title': f'Sample Market Analysis: {symbol} Stock Performance',
                'summary': f'This is a sample news article about {symbol}\'s recent market performance and future outlook.',
                'url': 'https://example.com',
                'published_date': datetime.now().isoformat(),
                'source': 'Sample Financial News',
                'image_url': ''
            },
            {
                'title': f'Industry Trends Affecting {symbol}',
                'summary': f'Analysis of how current industry trends might impact {symbol}\'s business strategy and market position.',
                'url': 'https://example.com',
                'published_date': (datetime.now() - timedelta(days=1)).isoformat(),
                'source': 'Sample Market News',
                'image_url': ''
            },
            {
                'title': f'Quarterly Earnings Preview: {symbol}',
                'summary': f'What to expect from {symbol}\'s upcoming quarterly earnings report and key metrics to watch.',
                'url': 'https://example.com',
                'published_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'source': 'Sample Financial Analysis',
                'image_url': ''
            }
        ]
    
    base_url = 'https://newsapi.org/v2/everything'
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    params = {
        'q': f'"{symbol}" AND (stock OR shares OR market)',
        'from': start_date.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'relevancy',
        'apiKey': api_key,
        'pageSize': 10
    }
    
    try:
        print(f"Making request to NewsAPI for {symbol}")
        response = requests.get(base_url, params=params)
        print(f"Response status code: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 401:
            print("API key error - check if NEWS_API_KEY is set correctly")
            return []
            
        if 'status' in data and data['status'] == 'error':
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return []
        
        if 'articles' in data and data['articles']:
            news_items = []
            for article in data['articles'][:10]:  # Limit to 10 items
                try:
                    news_items.append({
                        'title': article['title'],
                        'summary': article.get('description', 'Click to read more...'),
                        'url': article['url'],
                        'published_date': article['publishedAt'],
                        'source': article.get('source', {}).get('name', 'News Source'),
                        'image_url': article.get('urlToImage', '')
                    })
                except Exception as e:
                    print(f"Error processing news item: {e}")
                    continue
            
            print(f"Successfully processed {len(news_items)} news items")
            return news_items
        
        print("No news items found in response")
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

@csrf_exempt
def company_news(request):
    if request.method == 'GET':
        symbol = request.GET.get('symbol', '').strip().upper()
        if not symbol:
            return JsonResponse({
                'error': 'Stock symbol is required'
            }, status=400)
        
        print(f"Fetching news for symbol: {symbol}")
        news_items = get_company_news(symbol)
        
        if not news_items:
            print("No news found for symbol, trying market news")
            # If no news found, try to get general market news
            news_items = get_company_news('MARKET')
        
        return JsonResponse({
            'news': news_items
        })
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)

def get_news(company_name):
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        print("Warning: NEWS_API_KEY not found in environment variables")
        return None
        
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={api_key}&pageSize=5"
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 401:
            print("Invalid News API key")
            return None
            
        print(f"News API Response status: {response.status_code}")
        return data
    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

@csrf_exempt
def fetch_news(request):
    if request.method == 'GET':
        company_name = request.GET.get('company_name', '')
        if not company_name:
            return JsonResponse({
                'error': 'Company name is required'
            }, status=400)
            
        # Try to get news from API
        news_data = get_news(company_name)
        
        # If API fails, return sample data for testing
        if not news_data or 'articles' not in news_data:
            # Return sample data for testing
            return JsonResponse({
                'articles': [
                    {
                        'title': f'Sample news about {company_name}',
                        'description': f'This is a sample news article about {company_name} for testing purposes.',
                        'url': 'https://example.com',
                        'publishedAt': '2023-07-10T12:00:00Z'
                    },
                    {
                        'title': f'Another news about {company_name}',
                        'description': f'Second sample news article about {company_name}.',
                        'url': 'https://example.com',
                        'publishedAt': '2023-07-09T09:30:00Z'
                    }
                ]
            })
        
        return JsonResponse(news_data)
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check if username already exists
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                }, status=400)
                
            # Check if email already exists
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                }, status=400)
            
            # Create new user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # If fullName is provided, split it into first_name and last_name
            if 'fullName' in data and data['fullName']:
                name_parts = data['fullName'].split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.save()
            
            # Log the user in after signup
            login(request, user)
                
            return JsonResponse({
                'success': True,
                'message': 'User created successfully'
            })
            
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'message': f'Missing required field: {str(e)}'
            }, status=400)
            
        except Exception as e:
            print('Error:', str(e))  # Add this for debugging
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = authenticate(
                username=data['username'],
                password=data['password']
            )
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful'
                })
            return JsonResponse({
                'success': False, 
                'message': 'Invalid credentials'
            }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'message': f'Missing field: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Login error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def search_stock(request):
    if request.method == 'GET':
        query = request.GET.get('query', '').strip().upper()
        if not query:
            return JsonResponse({
                'error': 'Search query is required'
            }, status=400)
        
        # Search for stocks matching the query
        stocks = Stock.objects.filter(
            models.Q(symbol__icontains=query) | models.Q(name__icontains=query)
        )[:10]  # Limit to 10 results
        
        # If no stocks found in database, use a basic list of common stocks
        if not stocks:
            # Fallback for testing or when DB is empty
            common_stocks = [
                {'symbol': 'AAPL', 'name': 'Apple Inc.'},
                {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
                {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
                {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
                {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
                {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
                {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
                {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
                {'symbol': 'V', 'name': 'Visa Inc.'},
                {'symbol': 'WMT', 'name': 'Walmart Inc.'},
            ]
            
            # Filter common stocks based on query
            filtered_stocks = [
                stock for stock in common_stocks
                if query in stock['symbol'] or query.lower() in stock['name'].lower()
            ]
            
            return JsonResponse({
                'results': filtered_stocks
            })
        
        # Format the database results
        results = [
            {'symbol': stock.symbol, 'name': stock.name}
            for stock in stocks
        ]
        
        return JsonResponse({
            'results': results
        })
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)

def get_cached_stock_data(symbol, extended_cache=False):
    """Helper function to get or set cached stock data"""
    cache_key = f'stock_data_{symbol}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"Cache hit for {symbol}")
        return cached_data
        
    print(f"Cache miss for {symbol}, fetching from API")
    
    # Try up to 3 times to get the data
    max_retries = 3
    retry_delay = 2  # seconds
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("Warning: ALPHA_VANTAGE_API_KEY not found in environment variables")
        return generate_mock_stock_data(symbol)
    
    ts = TimeSeries(key=api_key, output_format='pandas')
    
    for attempt in range(max_retries):
        try:
            # Get current quote
            quote, _ = ts.get_quote_endpoint(symbol=symbol)
            
            if quote.empty:
                raise ValueError("Invalid data received from Alpha Vantage")
            
            # Extract the required data
            stock_data = {
                'symbol': symbol,
                'name': get_company_name(symbol),
                'price': float(quote['05. price']),
                'change': float(quote['09. change']),
            }
            
            # Get historical data
            hist_data = get_stock_history(symbol)
            if hist_data:
                stock_data['historicalData'] = hist_data
            else:
                stock_data['historicalData'] = generate_mock_history_data(stock_data['price'])
            
            # Cache for longer if it's a popular stock
            timeout = 1800 if extended_cache else 300  # 30 minutes for popular stocks, 5 minutes for others
            cache.set(cache_key, stock_data, timeout=timeout)
            return stock_data
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            continue
    
    # If all retries failed, use mock data
    mock_data = generate_mock_stock_data(symbol)
    cache.set(cache_key, mock_data, timeout=60)  # Cache mock data for shorter time
    return mock_data

def generate_mock_stock_data(symbol):
    """Generate realistic-looking mock data when API fails"""
    base_prices = {
        'AAPL': 170.0,
        'MSFT': 330.0,
        'GOOGL': 125.0,
        'AMZN': 130.0,
        'META': 290.0,
        'TSLA': 180.0,
        'NVDA': 450.0,
        'JPM': 145.0
    }
    
    base_price = base_prices.get(symbol, 100.0)  # Default to 100 if symbol not found
    variation = random.uniform(-5, 5)
    price = base_price + (base_price * (variation / 100))
    
    return {
        'symbol': symbol,
        'name': get_company_name(symbol),
        'price': price,
        'change': variation,
        'historicalData': generate_mock_history_data(price)
    }

def get_company_name(symbol):
    """Get company name for common stocks"""
    companies = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'META': 'Meta Platforms Inc.',
        'TSLA': 'Tesla Inc.',
        'NVDA': 'NVIDIA Corporation',
        'JPM': 'JPMorgan Chase & Co.'
    }
    return companies.get(symbol, f'{symbol} Inc.')

def generate_mock_history_data(current_price, points=50):
    """Generate realistic-looking historical data"""
    data = []
    base_price = current_price
    volatility = 0.02  # 2% volatility
    
    for i in range(points):
        # Generate timestamp for last 24 hours
        time_point = datetime.now() - timedelta(hours=points-i)
        # Random walk with mean reversion
        change = random.gauss(0, volatility)
        base_price = base_price * (1 + change)
        
        data.append({
            'date': time_point.strftime('%H:%M'),
            'price': round(base_price, 2)
        })
    
    return data

def get_stock_history(symbol, period='1d', interval='5min'):
    """Get historical stock data with caching"""
    cache_key = f'stock_history_{symbol}_{period}_{interval}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"Cache hit for history of {symbol}")
        return cached_data
        
    print(f"Cache miss for history of {symbol}, fetching from API")
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return None
        
    ts = TimeSeries(key=api_key, output_format='pandas')
    
    try:
        if period == '1d':
            data, _ = ts.get_intraday(symbol=symbol, interval='5min', outputsize='full')
        else:
            data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
        
        if data.empty:
            return None
        
        history_data = [{
            'date': index.strftime('%H:%M'),
            'price': float(row['4. close'])
        } for index, row in data.iterrows()]
        
        # Cache for longer period
        cache.set(cache_key, history_data, timeout=1800)  # 30 minutes
        return history_data
        
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return None

@csrf_exempt
def popular_stocks(request):
    popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM']
    stocks_data = []
    
    # First, try to get all data from cache
    for symbol in popular_symbols:
        cached_data = cache.get(f'stock_data_{symbol}')
        if cached_data:
            stocks_data.append(cached_data)
    
    # If we have all the data from cache, return it immediately
    if len(stocks_data) == len(popular_symbols):
        return JsonResponse({'stocks': stocks_data})
    
    # If we're missing some data, fetch only what we need
    missing_symbols = [symbol for symbol in popular_symbols if not cache.get(f'stock_data_{symbol}')]
    
    try:
        for symbol in missing_symbols:
            try:
                # Add longer delay between requests for missing data
                if len(stocks_data) > 0:
                    time.sleep(1)  # Increased delay for missing data
                    
                stock_data = get_cached_stock_data(symbol, extended_cache=True)
                if stock_data:
                    stocks_data.append(stock_data)
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                # Add mock data if we fail to get real data
                mock_data = generate_mock_stock_data(symbol)
                stocks_data.append(mock_data)
                continue
        
        # Sort the data to maintain consistent order
        stocks_data.sort(key=lambda x: popular_symbols.index(x['symbol']))
        return JsonResponse({'stocks': stocks_data})
        
    except Exception as e:
        print(f"Error in popular_stocks view: {e}")
        # If everything fails, return mock data for all stocks
        mock_data = [generate_mock_stock_data(symbol) for symbol in popular_symbols]
        return JsonResponse({'stocks': mock_data})

@csrf_exempt
def watchlist(request):
    """
    GET: Retrieve user's watchlist
    POST: Add a stock to watchlist
    DELETE: Remove a stock from watchlist
    """
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    user = None
    
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            # In a real app, you'd validate the token and extract user info
            # For now, we'll just check if a token exists
            if token:
                # For testing, we'll use the first user
                user = User.objects.first()
        except Exception as e:
            print(f"Error validating token: {e}")
    
    # If no user is found, try to get the user from the session
    if not user and request.user.is_authenticated:
        user = request.user
    
    # If still no user, use the first user for testing purposes
    if not user:
        try:
            user = User.objects.first()
            if not user:
                print("No users found in the database")
                return JsonResponse({'error': 'Authentication required. No users found.'}, status=401)
        except Exception as e:
            print(f"Error getting default user: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    if request.method == 'GET':
        print(f"Getting watchlist for user: {user.username}")
        # Get all watchlist items for the user
        items = WatchlistItem.objects.filter(user=user)
        
        # Fetch details for each item from cache or Yahoo Finance
        stocks_data = []
        for item in items:
            try:
                # Add a shorter delay between requests since we have caching
                if len(stocks_data) > 0:  # Don't delay on first request
                    time.sleep(1)  # Reduced to 1 second since we have caching now
                
                stock_data = get_cached_stock_data(item.symbol)
                stocks_data.append(stock_data)
                    
            except Exception as e:
                print(f"Error processing {item.symbol}: {e}")
                continue
        
        return JsonResponse({
            'stocks': stocks_data
        })
    
    elif request.method == 'POST':
        try:
            print("Processing POST request to watchlist")
            body_unicode = request.body.decode('utf-8')
            print(f"Request body: {body_unicode}")
            data = json.loads(body_unicode)
            symbol = data.get('symbol', '').strip().upper()
            
            if not symbol:
                return JsonResponse({
                    'success': False,
                    'message': 'Stock symbol is required'
                }, status=400)
            
            print(f"Adding {symbol} to watchlist for user {user.username}")
            # Check if the stock already exists in the watchlist
            if WatchlistItem.objects.filter(user=user, symbol=symbol).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Stock already in watchlist'
                }, status=400)
            
            # Add to watchlist
            WatchlistItem.objects.create(user=user, symbol=symbol)
            print(f"Successfully added {symbol} to watchlist")
            
            return JsonResponse({
                'success': True,
                'message': f'{symbol} added to watchlist'
            })
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            print(f"Error in watchlist POST: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol', '').strip().upper()
            
            if not symbol:
                return JsonResponse({
                    'success': False,
                    'message': 'Stock symbol is required'
                }, status=400)
            
            # Remove from watchlist
            item = WatchlistItem.objects.filter(user=user, symbol=symbol)
            if item.exists():
                item.delete()
                return JsonResponse({
                    'success': True,
                    'message': f'{symbol} removed from watchlist'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Stock not found in watchlist'
                }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)

@csrf_exempt
def predict_stock(request):
    """
    My AI prediction endpoint that combines different analysis methods
    
    What it does:
    - Technical analysis using indicators
    - News sentiment stuff
    - Market data
    - Shows how confident the prediction is
    
    Added caching to make it faster (15 min cache)
    
    Args:
        request: Needs a stock symbol in the request
        
    Returns:
        JSON with prediction data, price targets and analysis
    """
    if request.method == 'GET':
        symbol = request.GET.get('symbol', '').strip().upper()
        if not symbol:
            return JsonResponse({
                'error': 'Stock symbol is required'
            }, status=400)
        
        # Check cache first
        cache_key = f'prediction_{symbol}'
        cached_prediction = cache.get(cache_key)
        if cached_prediction:
            print(f"Using cached prediction for {symbol}")
            return JsonResponse(cached_prediction)
            
        try:
            # Get prediction for the stock
            prediction = get_stock_prediction(symbol)
            
            if 'error' not in prediction:
                # Cache successful predictions for 15 minutes
                cache.set(cache_key, prediction, timeout=900)
            
            return JsonResponse(prediction)
            
        except Exception as e:
            print(f"Error in predict_stock for {symbol}: {e}")
            return JsonResponse({
                'error': 'Failed to generate prediction. Please try again later.',
                'details': str(e)
            }, status=500)
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)
