import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

function LandingPage() {
  const [sampleStocks, setSampleStocks] = useState([
    { symbol: 'AAPL', name: 'Apple Inc.', price: 189.43, change: 1.25 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', price: 415.23, change: 0.78 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 176.84, change: -0.45 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 185.37, change: 2.13 },
    { symbol: 'META', name: 'Meta Platforms Inc.', price: 495.71, change: -1.02 },
    { symbol: 'TSLA', name: 'Tesla Inc.', price: 212.19, change: 3.45 }
  ]);

  return (
    <div className="landing-page">
      <header className="landing-header">
        <h1>Market Echo</h1>
        <p>Your intelligent stock market companion</p>
      </header>
      
      <div className="features-section">
        <div className="feature-card">
          <h3>Real-time Stock Data</h3>
          <p>Get up-to-date information on your favorite stocks</p>
        </div>
        <div className="feature-card">
          <h3>AI-Powered Predictions</h3>
          <p>Make informed decisions with our advanced prediction models</p>
        </div>
        <div className="feature-card">
          <h3>Personalized Watchlist</h3>
          <p>Track and manage your favorite stocks in one place</p>
        </div>
      </div>

      <div className="cta-section">
        <h2>Ready to start predicting?</h2>
        <div className="auth-buttons">
          <Link to="/login" className="auth-button login">Login</Link>
          <Link to="/signup" className="auth-button signup">Sign Up</Link>
        </div>
      </div>

      <div className="popular-stocks-preview">
        <h2>Popular Stocks</h2>
        <div className="stocks-grid">
          {sampleStocks.map((stock) => (
            <div key={stock.symbol} className="stock-preview">
              <h3>{stock.symbol}</h3>
              <p>{stock.name}</p>
              <div className={`stock-price-preview ${stock.change > 0 ? 'positive' : 'negative'}`}>
                ${stock.price.toFixed(2)}
                <span>{stock.change > 0 ? '↑' : '↓'} {Math.abs(stock.change).toFixed(2)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LandingPage; 