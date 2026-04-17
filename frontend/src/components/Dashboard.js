/**
 * Dashboard Component
 * 
 * Main interface for authenticated users to view and interact with stock data.
 * Provides real-time stock monitoring, watchlist management, and stock predictions.
 * 
 * Features:
 * - Real-time stock price updates
 * - Watchlist management
 * - Stock search functionality
 * - AI-powered price predictions
 * - Technical analysis indicators
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StockWidget from './StockWidget';
import ChartModal from './ChartModal';
import './Dashboard.css';

function Dashboard({ onLogout, popularStocks: propPopularStocks }) {
  const [popularStocks, setPopularStocks] = useState(propPopularStocks || []);
  const [watchlist, setWatchlist] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  /**
   * Fetch user's watchlist on component mount
   * Implements authentication check and error handling
   */
  useEffect(() => {
    if (propPopularStocks) {
      setPopularStocks(propPopularStocks);
    } else {
      fetchPopularStocks();
    }
    fetchWatchlist();
  }, [propPopularStocks]);

  const fetchPopularStocks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/popular-stocks/');
      const data = await response.json();
      if (data.stocks) {
        setPopularStocks(data.stocks);
      }
    } catch (error) {
      console.error('Error fetching popular stocks:', error);
    }
  };

  /**
   * Fetch and update watchlist data
   * Handles API communication and state updates
   */
  const fetchWatchlist = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/watchlist/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.stocks) {
        setWatchlist(data.stocks);
      } else if (data.error) {
        console.error('Error fetching watchlist:', data.error);
      }
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    }
  };

  /**
   * Search for stocks based on user input
   * Implements debounced API calls and result filtering
   * 
   * @param {string} query - Search term entered by user
   */
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/search-stock/?query=${searchQuery}`);
      const data = await response.json();
      if (data.results) {
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error('Error searching stocks:', error);
    }
  };

  /**
   * Add stock to user's watchlist
   * Updates both backend and local state
   * 
   * @param {string} symbol - Stock symbol to add
   */
  const addToWatchlist = async (symbol) => {
    console.log(`Attempting to add ${symbol} to watchlist`);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        alert('Please log in to add stocks to your watchlist');
        return;
      }

      console.log(`Sending request to add ${symbol} to watchlist`);
      const response = await fetch('http://localhost:8000/api/watchlist/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ symbol }),
      });
      
      console.log(`Response status for ${symbol}: ${response.status}`);
      const data = await response.json();
      console.log(`Response data:`, data);
      
      if (response.ok) {
        console.log(`Successfully added ${symbol} to watchlist`);
        fetchWatchlist();
        // Clear search results after adding to watchlist
        setSearchResults([]);
        setSearchQuery('');
        // Show success notification (could be enhanced with a toast notification)
        alert(`${symbol} added to your watchlist!`);
      } else {
        console.error(`Error adding ${symbol} to watchlist:`, data);
        alert(`Error: ${data.message || 'Failed to add stock to watchlist'}`);
      }
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Error adding stock to watchlist. Please try again.');
    }
  };

  /**
   * Remove stock from watchlist
   * Handles both API call and local state update
   * 
   * @param {string} symbol - Stock symbol to remove
   */
  const removeFromWatchlist = async (symbol) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        alert('Please log in to remove stocks from your watchlist');
        return;
      }

      const response = await fetch('http://localhost:8000/api/watchlist/', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ symbol }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log(`Successfully removed ${symbol} from watchlist`);
        setWatchlist(watchlist.filter(stock => stock.symbol !== symbol));
        alert(`${symbol} removed from your watchlist!`);
      } else {
        console.error(`Error removing ${symbol} from watchlist:`, data);
        alert(`Error: ${data.message || 'Failed to remove stock from watchlist'}`);
      }
    } catch (error) {
      console.error('Error removing from watchlist:', error);
      alert('Error removing stock from watchlist. Please try again.');
    }
  };

  /**
   * Open detailed chart modal for selected stock
   * Updates modal state and fetches detailed data
   * 
   * @param {Object} stock - Stock data object
   */
  const handleStockClick = (stock) => {
    // ... existing code ...
  };

  const handleLogout = () => {
    // First call the passed onLogout function to clear authentication state
    onLogout();
    
    // Then manually navigate to the landing page
    window.location.href = '/';
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-top">
          <div className="header-title">Market Echo</div>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="search-section">
          <form onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit">Search</button>
          </form>
          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((stock) => (
                <div key={stock.symbol} className="search-result">
                  <span>{stock.symbol} - {stock.name}</span>
                  <button onClick={() => addToWatchlist(stock.symbol)}>Add to Watchlist</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="watchlist-section">
          <h2>Your Watchlist</h2>
          {watchlist.length > 0 ? (
            <div className="stocks-grid">
              {watchlist.map((stock) => (
                <StockWidget 
                  key={stock.symbol} 
                  stock={stock} 
                  onAddToWatchlist={addToWatchlist}
                  onRemoveFromWatchlist={removeFromWatchlist}
                  isInWatchlist={true}
                />
              ))}
            </div>
          ) : (
            <p className="empty-watchlist">Your watchlist is empty. Search for stocks and add them to your watchlist.</p>
          )}
        </div>

        <div className="popular-stocks-section">
          <h2>Popular Stocks</h2>
          <div className="stocks-grid">
            {popularStocks.map((stock) => (
              <StockWidget 
                key={stock.symbol} 
                stock={stock} 
                onAddToWatchlist={addToWatchlist}
                isInWatchlist={watchlist.some(item => item.symbol === stock.symbol)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 