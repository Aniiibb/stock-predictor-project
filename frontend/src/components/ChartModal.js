/**
 * Chart popup for showing detailed stock info
 * 
 * Shows a nice interactive chart with:
 * - Price history
 * - Technical indicators
 * - AI predictions
 * - News and sentiment
 * - Real-time updates
 */

import React, { useState, useEffect } from 'react';
import './ChartModal.css';
import StockChart from './StockChart';

function ChartModal({ stock, onClose, onAddToWatchlist, onRemoveFromWatchlist, isInWatchlist }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPrediction, setShowPrediction] = useState(false);
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);
  const [technicalData, setTechnicalData] = useState(null);
  const [error, setError] = useState(null);

  /**
   * Gets all the analysis data when component loads
   * Includes predictions, news and technical stuff
   */
  useEffect(() => {
    fetchAnalysisData();
  }, [stock.symbol]);

  /**
   * Gets AI prediction for the stock price
   * Combines technical and sentiment analysis
   * 
   * @param symbol - Stock to predict
   * @returns Prediction data with confidence levels
   */
  const fetchPrediction = async (symbol) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/predict-stock/?symbol=${symbol}`);
      const data = await response.json();
      
      if (response.ok) {
        setPrediction(data);
      } else {
        console.error('Error fetching prediction:', data.error);
        setPrediction({ error: data.error || 'Failed to generate prediction' });
      }
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction({ error: 'Network error while fetching prediction' });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch recent news articles and sentiment analysis
   * Analyzes news sentiment impact on stock price
   * 
   * @param {string} symbol - Stock symbol to get news for
   * @returns {Array} News articles with sentiment scores
   */
  const fetchNews = async (symbol) => {
    setLoadingNews(true);
    try {
      const response = await fetch(`http://localhost:8000/api/company-news/?symbol=${symbol}`);
      const data = await response.json();
      
      if (response.ok) {
        setNews(data.news || []);
      } else {
        console.error('Error fetching news:', data.error);
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoadingNews(false);
    }
  };

  /**
   * Calculate and format technical indicators
   * Processes raw stock data into technical analysis metrics
   * 
   * @param {Object} stockData - Raw stock price and volume data
   * @returns {Object} Formatted technical indicators
   */
  const processTechnicalData = (stockData) => {
    // ... existing code ...
  };

  /**
   * Fetch all analysis data in parallel
   * Coordinates multiple API calls and state updates
   */
  const fetchAnalysisData = async () => {
    // ... existing code ...
  };

  const handleShowPrediction = () => {
    if (!prediction && stock && stock.symbol) {
      fetchPrediction(stock.symbol);
    }
    setShowPrediction(true);
  };

  if (!stock) return null;

  const handleAddToWatchlist = () => {
    onAddToWatchlist(stock.symbol);
  };

  const handleRemoveFromWatchlist = () => {
    if (onRemoveFromWatchlist) {
      onRemoveFromWatchlist(stock.symbol);
      onClose();
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="chart-modal-overlay">
      <div className="chart-modal">
        <div className="chart-modal-header">
          <div className="chart-modal-title">
            <h2>{stock.symbol}</h2>
            <p>{stock.name}</p>
          </div>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="chart-modal-price">
          <div className={`price-display ${stock.change > 0 ? 'positive' : 'negative'}`}>
            ${stock.price.toFixed(2)}
            <span className="change-indicator">
              {stock.change > 0 ? '↑' : '↓'} {Math.abs(stock.change).toFixed(2)}%
            </span>
          </div>
          {!isInWatchlist ? (
            <button 
              className="add-watchlist-button"
              onClick={handleAddToWatchlist}
            >
              Add to Watchlist
            </button>
          ) : (
            <button 
              className="remove-watchlist-button"
              onClick={handleRemoveFromWatchlist}
            >
              Remove from Watchlist
            </button>
          )}
        </div>
        
        <div className="chart-modal-chart">
          <StockChart 
            data={{
              labels: stock.historicalData?.map(point => point.date),
              values: stock.historicalData?.map(point => point.price)
            }}
            isPositive={stock.change > 0}
            height={300}
          />
        </div>

        <div className="chart-modal-stats">
          {!loading && prediction && prediction.metrics && (
            <>
              <div className="stat-item">
                <span className="stat-label">P/E Ratio</span>
                <span className="stat-value">{prediction.metrics.pe_ratio}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Market Cap</span>
                <span className="stat-value">
                  {typeof prediction.metrics.market_cap === 'number' 
                    ? `$${(prediction.metrics.market_cap / 1000000000).toFixed(2)}B` 
                    : prediction.metrics.market_cap}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Dividend Yield</span>
                <span className="stat-value">
                  {typeof prediction.metrics.dividend_yield === 'number' 
                    ? `${(prediction.metrics.dividend_yield * 100).toFixed(2)}%` 
                    : prediction.metrics.dividend_yield}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Avg Volume</span>
                <span className="stat-value">
                  {typeof prediction.metrics.avg_volume === 'number' 
                    ? `${(prediction.metrics.avg_volume / 1000000).toFixed(2)}M` 
                    : prediction.metrics.avg_volume}
                </span>
              </div>
              {prediction.prediction && (
                <div className="stat-item">
                  <span className="stat-label">Prediction</span>
                  <span className={`stat-value ${prediction.prediction.direction === 'up' ? 'positive' : 'negative'}`}>
                    {prediction.prediction.direction === 'up' ? '↑' : '↓'} {Math.abs(prediction.prediction.percentage || 0).toFixed(2)}%
                  </span>
                </div>
              )}
            </>
          )}
          {loading && showPrediction && (
            <div className="stat-item loading-stats">
              <span className="stat-label">Loading stats...</span>
            </div>
          )}
          {!showPrediction && (
            <div className="stats-placeholder">
              <p>Show AI prediction to see detailed stock metrics</p>
            </div>
          )}
        </div>

        <div className="chart-modal-prediction">
          <h3>AI Prediction</h3>
          {!showPrediction ? (
            <div className="prediction-button-container">
              <button 
                className="show-prediction-button"
                onClick={handleShowPrediction}
              >
                Get AI Prediction
              </button>
            </div>
          ) : (
            <>
              {loading && (
                <div className="prediction-loading">
                  <p>Analyzing market data and generating prediction...</p>
                  <div className="loading-spinner"></div>
                </div>
              )}
              {!loading && prediction && prediction.prediction && (
                <p className={prediction.prediction.direction === 'up' ? 'positive' : 'negative'}>
                  {prediction.message}
                </p>
              )}
              {!loading && prediction && prediction.error && (
                <div className="prediction-error">
                  <p>Error: {prediction.error}</p>
                  <p>Please try again in a few minutes. This could be due to rate limiting or temporary server issues.</p>
                </div>
              )}
              {!loading && !prediction && (
                <p className="prediction-error">Unable to generate prediction at this time. Please try again later.</p>
              )}
            </>
          )}
        </div>

        <div className="chart-modal-news">
          <h3>Recent News</h3>
          {loadingNews ? (
            <div className="news-loading">
              <div className="loading-spinner"></div>
            </div>
          ) : news.length > 0 ? (
            <div className="news-list">
              {news.map((article, index) => (
                <a 
                  key={index}
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-item"
                >
                  <div className="news-content">
                    <h4>{article.title}</h4>
                    <p>{article.summary}</p>
                    <span className="news-date">{formatDate(article.published_date)}</span>
                  </div>
                  {article.image_url && (
                    <div className="news-image">
                      <img src={article.image_url} alt={article.title} />
                    </div>
                  )}
                </a>
              ))}
            </div>
          ) : (
            <p className="no-news">No recent news available for {stock.name}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChartModal; 