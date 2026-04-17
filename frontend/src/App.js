/**
 * Main Application Component
 * 
 * This is the root component of the stock prediction application.
 * It handles routing, authentication state, and real-time stock data updates.
 * 
 * Features:
 * - Authentication management
 * - Real-time stock data polling
 * - Route protection
 * - Global state management
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import LoginSignup from './LoginSignup';
import './App.css';
import StockWidget from './components/StockWidget';

function App() {
  // Authentication and user state management
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [news, setNews] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [popularStocks, setPopularStocks] = useState([]);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [error, setError] = useState(null);

  // Fetch popular stocks on component mount and set up polling
  useEffect(() => {
    // Clear any existing token on initial load
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setIsAuthChecking(false);
    fetchPopularStocks();
    // Set up polling for real-time updates
    const interval = setInterval(fetchPopularStocks, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  /**
   * Fetch popular stocks data from the backend
   * Implements error handling and state updates
   */
  const fetchPopularStocks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/popular-stocks/');
      const data = await response.json();
      
      if (data.stocks) {
        console.log('Received stock data:', data.stocks);
        setPopularStocks(data.stocks);
      }
    } catch (error) {
      console.error('Error fetching popular stocks:', error);
    }
  };

  /**
   * Verify user authentication status
   * Updates authentication state and handles loading state
   */
  const checkAuth = async () => {
    // ... existing code ...
  };

  /**
   * Handle user login
   * Updates authentication state and redirects to dashboard
   */
  const handleLogin = (token) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
  };

  /**
   * Handle user logout
   * Clears authentication state and redirects to landing page
   */
  const handleLogout = () => {
    // Clear user state
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setPrediction(null);
    setNews([]);
    setSearchResults([]);
  };

  const fetchPrediction = async () => {
    setIsLoading(true);
    try {
      console.log(`Fetching prediction for: ${symbol}`);
      
      const response = await fetch(`http://localhost:8000/api/fetch-news/?company_name=${symbol}`);
      console.log("Response status:", response.status);
      
      const data = await response.json();
      console.log("Response data:", data);
      
      if (data.articles && data.articles.length > 0) {
        setPrediction(`Based on recent news and trends for ${symbol}`);
        setNews(data.articles);
      } else if (data.error) {
        console.error('API Error:', data.error);
        setPrediction(`Error: ${data.error}`);
        setNews([]);
      } else {
        console.error('No articles found in response');
        setPrediction(`No news found for ${symbol}`);
        setNews([]);
      }
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction(`Error fetching data. Please try again.`);
      setNews([]);
    } finally {
      setIsLoading(false);
    }
  };

  const searchStock = async () => {
    setIsSearching(true);
    try {
      console.log(`Searching for stock: ${symbol}`);
      
      // gets data from api
      const response = await fetch(`http://localhost:8000/api/search-stock/?query=${symbol}`);
      console.log("Response status:", response.status);
      
      const data = await response.json();
      console.log("Search results:", data);
      
      if (data.results && data.results.length > 0) {
        setSearchResults(data.results);
      } else {
        setSearchResults([]);
        // Show a message that no stocks were found
        setPrediction(`No stocks found matching "${symbol}"`);
      }
    } catch (error) {
      console.error('Error searching for stocks:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // When user selects a stock from search results
  const selectStock = async (stockSymbol, stockName) => {
    setSymbol(stockSymbol);
    setSearchResults([]);
    
    // Now fetch the prediction for the selected stock
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/fetch-news/?company_name=${stockSymbol}`);
      const data = await response.json();
      
      if (data.articles && data.articles.length > 0) {
        setPrediction(`Based on recent news and trends for ${stockName} (${stockSymbol})`);
        setNews(data.articles);
      } else if (data.error) {
        setPrediction(`Error: ${data.error}`);
        setNews([]);
      } else {
        setPrediction(`No news found for ${stockName} (${stockSymbol})`);
        setNews([]);
      }
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction(`Error fetching data. Please try again.`);
      setNews([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Wait for auth check before rendering routes
  if (isAuthChecking) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
                <Navigate to="/dashboard" /> : 
                <LandingPage />
            } 
          />
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
                <Navigate to="/dashboard" /> : 
                <LoginSignup onLogin={handleLogin} isLogin={true} />
            } 
          />
          <Route 
            path="/signup" 
            element={
              isAuthenticated ? 
                <Navigate to="/dashboard" /> : 
                <LoginSignup onLogin={handleLogin} isLogin={false} />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              isAuthenticated ? 
                <Dashboard onLogout={handleLogout} popularStocks={popularStocks} /> : 
                <Navigate to="/login" />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
