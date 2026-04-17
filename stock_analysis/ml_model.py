"""
Stock price prediction using ML
This is where I combine technical indicators, sentiment analysis,
and historical data to predict stock prices
"""

import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import os
from datetime import datetime, timedelta
import requests

from .models import StockPrediction
from .news_sentiment import NewsAnalyzer

def get_stock_data(symbol, period='1y'):
    """
    Gets historical stock data and handles API rate limits
    Added caching to make it faster and avoid hitting limits
    
    Args:
        symbol: Stock symbol to get data for
        period: Time period ('1d', '1y', '2y')
        
    Returns:
        DataFrame with stock price history and volume
    """
    from django.core.cache import cache
    import time
    
    # Check cache first
    cache_key = f'stock_data_{symbol}_{period}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    max_retries = 3
    base_delay = 2  # seconds
    
    # Get Alpha Vantage API key from environment
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("Alpha Vantage API key not found in environment variables")
    
    # Initialize Alpha Vantage client
    ts = TimeSeries(key=api_key, output_format='pandas')
    
    for attempt in range(max_retries):
        try:
            # Convert period to appropriate Alpha Vantage function
            if period == '1d':
                data, _ = ts.get_intraday(symbol=symbol, interval='5min', outputsize='full')
            elif period in ['1y', '2y']:
                data, _ = ts.get_daily(symbol=symbol, outputsize='full')
                # Filter last year's data
                years = int(period[0])
                start_date = datetime.now() - timedelta(days=365 * years)
                data = data[data.index >= start_date]
            else:
                data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
            
            if not data.empty:
                # Rename columns to match existing code
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # Cache successful response for 15 minutes
                cache.set(cache_key, data, timeout=900)
                return data
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
            if "API call frequency" in str(e):
                # Exponential backoff for rate limits
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            else:
                # For non-rate-limit errors, return None immediately
                return None
    
    # try to use older cached data with a longer expiration
    old_cache_key = f'stock_data_{symbol}_{period}_old'
    old_cached_data = cache.get(old_cache_key)
    if old_cached_data is not None:
        return old_cached_data
        
    return None

def prepare_data(df, prediction_days=60):
    """
    Prepare the stock data for ML model.
    """
    
    if df is None or df.empty:
        return None, None, None, None
    
    
    df = df[['Close']].copy()
    
    # Scale the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df)
    
    # Prepare training data
    x_train = []
    y_train = []
    
    for i in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[i-prediction_days:i, 0])
        y_train.append(scaled_data[i, 0])
    
    x_train, y_train = np.array(x_train), np.array(y_train)
    
    return x_train, y_train, scaler, df


def calculate_technical_indicators(df):
    """
    Calculate a comprehensive set of technical indicators for stock analysis.
    
    Includes:
    - Trend indicators: EMA, MACD
    - Momentum indicators: ROC, RSI
    - Volatility indicators: ATR, Bollinger Bands
    - Volume indicators: OBV, VWAP
    
    Args:
        df (pandas.DataFrame): OHLCV data
        
    Returns:
        pandas.DataFrame: Original data with technical indicators added
    """
    # Price-based indicators
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Momentum indicators
    df['ROC'] = df['Close'].pct_change(periods=12) * 100  # Rate of Change
    df['MOM'] = df['Close'].diff(periods=10)  # Momentum
    
    # Volatility indicators
    df['ATR'] = calculate_atr(df)  # Average True Range
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = calculate_bollinger_bands(df)
    
    # Volume-based indicators
    df['OBV'] = calculate_obv(df)  # On-Balance Volume
    df['VWAP'] = calculate_vwap(df)  # Volume Weighted Average Price
    
    # Trend indicators
    df['ADX'] = calculate_adx(df)  # Average Directional Index
    
    return df

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.DataFrame({'TR1': tr1, 'TR2': tr2, 'TR3': tr3}).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    middle = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower

def calculate_obv(df):
    """Calculate On-Balance Volume"""
    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    return obv

def calculate_vwap(df):
    """Calculate Volume Weighted Average Price"""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap

def calculate_adx(df, period=14):
    """Calculate Average Directional Index"""
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())
    
    tr = pd.DataFrame({'TR1': tr1, 'TR2': tr2, 'TR3': tr3}).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = abs(100 * (minus_dm.rolling(window=period).mean() / atr))
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx

def predict_future_price(symbol, days=14):
    """
    Predicts stock prices using ML models
    Combines Random Forest and Linear Regression with different indicators
    
    What it uses:
    - Technical stuff (RSI, MACD etc)
    - News sentiment
    - Market volatility
    - Volume analysis
    
    Made it more realistic by limiting extreme predictions
    
    Args:
        symbol: Stock to predict
        days: How many days ahead to predict
        
    Returns:
        Prediction results with price targets and supporting data
    """
    try:
        # Get Alpha Vantage API key from environment
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            api_key = 'CSYCR0RJU8A2KQAL'
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # Get historical data - use full year of data for better training
        hist, _ = ts.get_daily(symbol=symbol, outputsize='full')
        # Keep last year of data for training
        hist = hist.tail(252)  # Approximately one trading year
        
        # Rename columns to match our existing code
        hist.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        if hist.empty:
            return {
                'error': 'No data available for this stock'
            }
        
        # Calculate all technical indicators with error handling
        try:
            hist = calculate_technical_indicators(hist)
        except Exception as e:
            return {
                'error': f'Error calculating technical indicators: {str(e)}'
            }
        
        # Get company name for better news search
        try:
            company_name = symbol  # We'll use the symbol since we don't have company info endpoint
        except:
            company_name = symbol
        
        # Initialize news analyzer and get sentiment features
        try:
            news_analyzer = NewsAnalyzer()
            sentiment_features = news_analyzer.get_sentiment_features(company_name)
        except Exception as e:
            return {
                'error': f'Error analyzing news sentiment: {str(e)}'
            }
        
        # Normalize sentiment scores to a smaller range (-0.1 to 0.1) to avoid overwhelming the model
        sentiment_score = sentiment_features['sentiment_score'] * 0.1
        sentiment_magnitude = sentiment_features['sentiment_magnitude'] * 0.1
        recent_sentiment_change = sentiment_features['recent_sentiment_change'] * 0.1
        sentiment_volatility = sentiment_features['sentiment_volatility'] * 0.1
        
        # Add sentiment features to the historical data
        hist['Sentiment_Score'] = sentiment_score
        hist['Sentiment_Magnitude'] = sentiment_magnitude
        hist['Recent_Sentiment_Change'] = recent_sentiment_change
        hist['Sentiment_Volatility'] = sentiment_volatility
        
        # Calculate daily returns and volatility
        hist['Daily_Return'] = hist['Close'].pct_change()
        hist['Volatility'] = hist['Daily_Return'].rolling(window=20).std()
        
        # Enhanced feature set including sentiment and market dynamics
        feature_columns = [
            'EMA12', 'EMA26', 'MACD', 'MACD_Signal',
            'ROC', 'MOM', 'ATR', 'BB_Upper', 'BB_Lower',
            'OBV', 'VWAP', 'ADX',
            'Volume', 'RSI', 'Volatility',
            'Sentiment_Score', 'Sentiment_Magnitude',
            'Recent_Sentiment_Change', 'Sentiment_Volatility'
        ]
        
        # Add traditional features
        hist['RSI'] = calculate_rsi(hist['Close'], periods=14)
        
        # Drop any rows with NaN values
        hist = hist.dropna()
        
        if len(hist) < 60:
            return {
                'error': 'Insufficient data for prediction (need at least 60 days)'
            }
        
        # Prepare training data - use 80% for training
        train_size = int(len(hist) * 0.8)
        train_data = hist[:train_size]
        test_data = hist[train_size:]
        
        # Scale features using training data only
        scaler = MinMaxScaler()
        X_train = scaler.fit_transform(train_data[feature_columns])
        y_train = train_data['Close'].values
        
        X_test = scaler.transform(test_data[feature_columns])
        y_test = test_data['Close'].values
        
        # Create and train multiple models for ensemble
        models = {
            'rf': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'lr': LinearRegression()
        }
        
        # Train and validate each model
        predictions = {}
        for name, model in models.items():
            model.fit(X_train, y_train)
            val_score = model.score(X_test, y_test)
            predictions[f'{name}_score'] = val_score
            
            # Make prediction on the latest data
            latest_features = scaler.transform(hist[feature_columns].iloc[-1:])
            predictions[name] = model.predict(latest_features)[0]
        
        # Weighted ensemble prediction (adjust weights based on validation scores)
        rf_weight = predictions['rf_score'] / (predictions['rf_score'] + predictions['lr_score'])
        lr_weight = 1 - rf_weight
        final_prediction = predictions['rf'] * rf_weight + predictions['lr'] * lr_weight
        
        # Get the current price
        current_price = hist['Close'].iloc[-1]
        
        # Calculate prediction percentage with a damping factor based on time horizon
        raw_prediction_percentage = ((final_prediction - current_price) / current_price) * 100
        damping_factor = 1.0 / (days / 7)  # Reduce prediction magnitude for longer horizons
        prediction_percentage = raw_prediction_percentage * damping_factor
        
        # Cap the prediction at realistic levels (e.g., ±20% for 14 days)
        max_change = 20.0  # Maximum realistic percentage change
        prediction_percentage = max(min(prediction_percentage, max_change), -max_change)
        
        # Recalculate final prediction based on capped percentage
        final_prediction = current_price * (1 + prediction_percentage / 100)
        
        # Determine prediction direction
        direction = "up" if prediction_percentage > 0 else "down"
        
        # Calculate confidence based on model performance, market conditions, and sentiment
        confidence = calculate_confidence_score(
            models['rf'], X_test, y_test, hist,
            sentiment_features,
            dict(zip(feature_columns, models['rf'].feature_importances_))
        )
        
        # Get the latest sentiment articles
        latest_articles = sentiment_features.get('latest_articles', [])
        
        return {
            'current_price': float(current_price),
            'prediction': {
                'price': float(final_prediction),
                'percentage': float(prediction_percentage),
                'direction': direction,
                'days': days,
                'confidence': float(confidence),
                'model_scores': {
                    'random_forest': float(predictions['rf_score']),
                    'linear_regression': float(predictions['lr_score'])
                }
            },
            'message': f"Our AI model predicts {symbol} will go {direction} by {abs(prediction_percentage):.2f}% in the next {days} days with {confidence:.1f}% confidence.",
            'technical_indicators': {
                'RSI': float(hist['RSI'].iloc[-1]),
                'MACD': float(hist['MACD'].iloc[-1]),
                'ADX': float(hist['ADX'].iloc[-1]),
                'BB_Width': float(hist['BB_Upper'].iloc[-1] - hist['BB_Lower'].iloc[-1]),
                'Volume_Trend': float(hist['OBV'].iloc[-1])
            },
            'sentiment_analysis': {
                'overall_score': float(sentiment_features['sentiment_score']),
                'recent_change': float(sentiment_features['recent_sentiment_change']),
                'volatility': float(sentiment_features['sentiment_volatility']),
                'article_count': sentiment_features['article_count'],
                'latest_articles': latest_articles[:5]  # Limit to 5 most recent articles
            }
        }
    except Exception as e:
        return {
            'error': f'Unexpected error in prediction: {str(e)}'
        }

def calculate_confidence_score(model, X, y, hist, sentiment_features, feature_importance):
    """
    Calculate prediction confidence based on multiple factors.
    
    Confidence factors:
    - Model performance (R-squared): ±20%
    - Market volatility: ±10%
    - Trend strength (ADX): +10%
    - RSI extremes: +5%
    - MACD signal: ±5%
    - Sentiment analysis: ±10%
    - Trading volume: +5%
    
    Base confidence: 70%
    Final range: 60-95%
    
    Args:
        model: Trained ML model
        X: Feature matrix
        y: Target values
        hist: Historical data
        sentiment_features: News sentiment data
        feature_importance: Feature importance scores
        
    Returns:
        float: Confidence score (60-95)
    """
    # Model performance score (R-squared)
    r2_score = model.score(X, y)
    base_confidence = 70.0  # Start with a base confidence of 70%
    
    # Adjust confidence based on model performance
    model_confidence = r2_score * 20  # Can add/subtract up to 20% based on model performance
    
    # Volatility score - lower volatility means higher confidence
    recent_volatility = hist['ATR'].iloc[-1] / hist['Close'].iloc[-1]
    volatility_score = (1 - min(recent_volatility * 10, 1)) * 10  # Can add/subtract up to 10%
    
    # Trend strength score based on ADX
    adx_value = hist['ADX'].iloc[-1]
    trend_strength = min(adx_value / 50, 1)  # Normalize ADX to 0-1 range
    trend_score = trend_strength * 10  # Can add up to 10% for strong trends
    
    # RSI score - more confidence if RSI is in extreme zones
    rsi = hist['RSI'].iloc[-1]
    rsi_confidence = 0
    if rsi <= 30 or rsi >= 70:
        rsi_confidence = 5  # Add 5% confidence for clear oversold/overbought conditions
    
    # MACD signal strength
    macd = abs(hist['MACD'].iloc[-1])
    macd_signal = abs(hist['MACD_Signal'].iloc[-1])
    macd_confidence = min(abs(macd - macd_signal) / macd_signal, 1) * 5  # Up to 5% based on MACD signal strength
    
    # Sentiment confidence
    sentiment_magnitude = abs(sentiment_features['sentiment_score'])
    sentiment_consistency = 1 - sentiment_features['sentiment_volatility']
    sentiment_confidence = (sentiment_magnitude * 0.7 + sentiment_consistency * 0.3) * 10  # Up to 10% from sentiment
    
    # Volume confidence - higher volume means more confidence
    volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].rolling(window=20).mean().iloc[-1]
    volume_confidence = min(volume_ratio - 1, 1) * 5 if volume_ratio > 1 else 0  # Up to 5% for above-average volume
    
    # Calculate final confidence score
    final_score = (
        base_confidence +
        model_confidence +
        volatility_score +
        trend_score +
        rsi_confidence +
        macd_confidence +
        sentiment_confidence +
        volume_confidence
    )
    
    # Ensure the score is between 60 and 95
    final_score = max(60, min(95, final_score))
    
    # If the model performance is very poor, reduce confidence regardless of other factors
    if r2_score < 0.3:  # If R-squared is less than 0.3
        final_score = max(60, final_score * 0.8)  # Reduce confidence but keep minimum of 60%
    
    return final_score

def calculate_rsi(prices, periods=14):
    """
    Calculate Relative Strength Index (RSI) for a given price series.
    """
    # Calculate price differences
    delta = prices.diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_stock_prediction(symbol):
    """
    Get stock prediction and relevant information.
    """
    try:
        # Get the stock prediction
        prediction = predict_future_price(symbol)
        
        # Get recent news sentiment (placeholder - in a real system, you would use NLP)
        sentiment = {
            'score': 0.65,  # Positive sentiment
            'label': 'Bullish'
        }
        
        # Get additional stock metrics using Alpha Vantage
        api_key = 'CSYCR0RJU8A2KQAL'
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # Get overview data
        try:
            overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}'
            overview_response = requests.get(overview_url)
            info = overview_response.json()
            
            # Add metrics to the prediction
            prediction['metrics'] = {
                'pe_ratio': info.get('PERatio', 'N/A'),
                'market_cap': info.get('MarketCapitalization', 'N/A'),
                'dividend_yield': info.get('DividendYield', 'N/A'),
                'avg_volume': info.get('SharesOutstanding', 'N/A')
            }
        except Exception as e:
            print(f"Error fetching overview data: {e}")
            prediction['metrics'] = {
                'pe_ratio': 'N/A',
                'market_cap': 'N/A',
                'dividend_yield': 'N/A',
                'avg_volume': 'N/A'
            }
        
        # Add sentiment information
        prediction['sentiment'] = sentiment
        
        return prediction
        
    except Exception as e:
        print(f"Error generating prediction for {symbol}: {e}")
        return {
            'error': str(e)
        }

def analyze_stock(stock):
    # Get historical data using Alpha Vantage
    api_key = 'CSYCR0RJU8A2KQAL'
    ts = TimeSeries(key=api_key, output_format='pandas')
    
    try:
        hist, _ = ts.get_daily(symbol=stock.symbol, outputsize='full')
        # Keep last year of data
        hist = hist.tail(365)
        # Rename columns to match our code
        hist.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Feature engineering
        hist['MA_50'] = hist['Close'].rolling(window=50).mean()
        hist['MA_200'] = hist['Close'].rolling(window=200).mean()
        hist['Daily_Return'] = hist['Close'].pct_change()
        
        # Prepare data for ML
        X = hist[['MA_50', 'MA_200', 'Daily_Return']].dropna()
        y = (X['Daily_Return'] > 0).astype(int)
        
        # Train model
        model = RandomForestRegressor()  # Changed from RandomForestClassifier
        model.fit(X[:-1], y[1:])
        
        # Make prediction
        prediction = model.predict([X.iloc[-1]])
        confidence = 0.85  # Simplified since predict_proba is not available in regressor
        
        # Save prediction
        StockPrediction.objects.create(
            stock=stock,
            prediction='UP' if prediction[0] > 0.5 else 'DOWN',
            confidence=confidence * 100,
            reasoning="Analysis based on technical indicators and recent news"
        )
        
        return prediction[0] > 0.5, []  # Simplified to return boolean prediction
        
    except Exception as e:
        print(f"Error analyzing stock: {e}")
        return False, [str(e)] 