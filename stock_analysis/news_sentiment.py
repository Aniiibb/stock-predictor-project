"""
News sentiment analysis stuff
Uses VADER and TextBlob to figure out if news is positive or negative
"""

import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from datetime import datetime, timedelta
import numpy as np

class NewsAnalyzer:
    def __init__(self):
        # Setting up VADER for analyzing financial news
        self.vader = SentimentIntensityAnalyzer()
        self.news_api_key = os.getenv('NEWS_API_KEY')  
        
    def get_news_articles(self, company_name, days=7):
        """
        Gets news articles about a company using NewsAPI
        
        Args:
            company_name: Company to look up
            days: How many days of news to get (default 7)
            
        Returns:
            List of news articles with their details
        """
        base_url = "https://newsapi.org/v2/everything"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'q': f'"{company_name}" AND (stock OR shares OR market)',
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'relevancy',
            'apiKey': self.news_api_key
        }
        
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                return response.json().get('articles', [])
            return []
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def analyze_article(self, article):
        """
        Analyzes one article using both VADER and TextBlob
        VADER is good for social media/news headlines
        TextBlob is good for general text analysis
        
        Args:
            article: The article data with title and description
            
        Returns:
            All the sentiment scores and article info
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        # VADER sentiment analysis
        vader_scores = self.vader.polarity_scores(text)
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        textblob_sentiment = blob.sentiment
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_pos': vader_scores['pos'],
            'vader_neg': vader_scores['neg'],
            'vader_neu': vader_scores['neu'],
            'textblob_polarity': textblob_sentiment.polarity,
            'textblob_subjectivity': textblob_sentiment.subjectivity,
            'published_at': article.get('publishedAt'),
            'url': article.get('url'),
            'title': article.get('title')
        }
    
    def get_sentiment_features(self, company_name, days=7):
        """
        Gets all the sentiment info from recent news
        Uses both VADER (70%) and TextBlob (30%) because VADER is better for finance
        
        Calculates:
        - Overall sentiment (-1 to 1)
        - How strong the sentiment is
        - If sentiment is changing recently
        - How much sentiment varies
        
        Args:
            company_name: Company to analyze
            days: Days of news to look at
            
        Returns:
            All the sentiment calculations and recent articles
        """
        articles = self.get_news_articles(company_name, days)
        if not articles:
            return {
                'sentiment_score': 0,
                'sentiment_magnitude': 0,
                'recent_sentiment_change': 0,
                'sentiment_volatility': 0,
                'article_count': 0
            }
        
        # Analyze all articles
        analyses = [self.analyze_article(article) for article in articles]
        
        # Sort by publication date
        analyses.sort(key=lambda x: x['published_at'])
        
        # Calculate various sentiment features
        vader_compounds = [a['vader_compound'] for a in analyses]
        textblob_polarities = [a['textblob_polarity'] for a in analyses]
        
        # Combine VADER and TextBlob scores with weighted average
        combined_sentiments = [(v * 0.7 + t * 0.3) for v, t in zip(vader_compounds, textblob_polarities)]
        
        # Calculate features
        sentiment_score = np.mean(combined_sentiments) if combined_sentiments else 0
        sentiment_magnitude = np.abs(sentiment_score)
        sentiment_volatility = np.std(combined_sentiments) if len(combined_sentiments) > 1 else 0
        
        # Calculate recent sentiment change (last 3 articles vs previous articles)
        if len(combined_sentiments) >= 6:
            recent_sentiment = np.mean(combined_sentiments[-3:])
            previous_sentiment = np.mean(combined_sentiments[:-3])
            recent_sentiment_change = recent_sentiment - previous_sentiment
        else:
            recent_sentiment_change = 0
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_magnitude': sentiment_magnitude,
            'recent_sentiment_change': recent_sentiment_change,
            'sentiment_volatility': sentiment_volatility,
            'article_count': len(articles),
            'latest_articles': analyses[-3:] if analyses else []  # Return latest 3 articles
        } 