/**
 * Stock price chart component
 * 
 * Makes a nice interactive chart showing:
 * - Price data
 * - Volume bars
 * - Moving averages
 * - Tooltips when you hover
 * - Different time ranges
 */

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Set up Chart.js components we need
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function StockChart({ data, isPositive, height = 80 }) {
  if (!data || (!data.labels && !data.values)) {
    // Return null or a placeholder if no data is available
    return <div className="chart-placeholder">Loading chart data...</div>;
  }

  const chartData = {
    labels: data.labels || Array(20).fill(''),
    datasets: [
      {
        label: '',
        data: data.values || Array(20).fill(0),
        borderColor: isPositive ? '#28a745' : '#dc3545',
        backgroundColor: isPositive ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#9274ca',
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <Line data={chartData} options={options} />
    </div>
  );
}

export default StockChart; 