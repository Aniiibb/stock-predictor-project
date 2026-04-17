import React, { useState } from 'react';
import StockChart from './StockChart';
import ChartModal from './ChartModal';

function StockWidget({ stock, onAddToWatchlist, onRemoveFromWatchlist, isInWatchlist }) {
  const [showModal, setShowModal] = useState(false);

  // Add data validation
  if (!stock) {
    return null;
  }

  const chartData = {
    labels: stock.historicalData?.map(point => point.date) || [],
    values: stock.historicalData?.map(point => point.price) || []
  };

  const handleWidgetClick = () => {
    console.log(`Opening modal for ${stock.symbol}`);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    console.log(`Closing modal for ${stock.symbol}`);
    setShowModal(false);
  };

  const handleAddToWatchlist = (symbol) => {
    console.log(`Adding ${symbol} to watchlist`);
    if (onAddToWatchlist) {
      onAddToWatchlist(symbol);
    } else {
      console.warn(`No onAddToWatchlist handler provided for ${symbol}`);
    }
    setShowModal(false);
  };

  const handleRemoveFromWatchlist = (e) => {
    e.stopPropagation(); // Prevent the widget click event from firing
    console.log(`Removing ${stock.symbol} from watchlist`);
    if (onRemoveFromWatchlist) {
      onRemoveFromWatchlist(stock.symbol);
    } else {
      console.warn(`No onRemoveFromWatchlist handler provided for ${stock.symbol}`);
    }
  };

  return (
    <>
      <div className="stock-widget" onClick={handleWidgetClick}>
        <div className="stock-header">
          <div className="stock-title">
            <h3>{stock.symbol}</h3>
            <p>{stock.name}</p>
          </div>
          <div className={`stock-price ${stock.change > 0 ? 'positive' : 'negative'}`}>
            ${stock.price?.toFixed(2)}
            <span>{stock.change > 0 ? '↑' : '↓'} {Math.abs(stock.change)?.toFixed(2)}%</span>
          </div>
        </div>
        <div className="stock-chart">
          <StockChart 
            data={chartData}
            isPositive={stock.change > 0}
          />
        </div>
        {isInWatchlist && (
          <button 
            className="remove-from-watchlist" 
            onClick={handleRemoveFromWatchlist}
            title="Remove from watchlist"
          >
            ×
          </button>
        )}
      </div>

      {showModal && (
        <ChartModal 
          stock={stock} 
          onClose={handleCloseModal} 
          onAddToWatchlist={handleAddToWatchlist}
          onRemoveFromWatchlist={onRemoveFromWatchlist}
          isInWatchlist={isInWatchlist}
        />
      )}
    </>
  );
}

export default StockWidget; 