import React, { useState, useEffect } from 'react';
import { processQuery, getQueryHistory } from '../services/api';

function QueryPanel({ onQueryResult }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  // Fetch history on initial component load
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const historyData = await getQueryHistory();
        setHistory(historyData.history.reverse()); // Show newest first
      } catch (err) {
        console.error('Failed to load history:', err);
      }
    };
    fetchHistory();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    
    try {
      const result = await processQuery(query);
      if (onQueryResult) {
        onQueryResult(result);
      }
      // Refresh history
      const historyData = await getQueryHistory();
      setHistory(historyData.history.reverse()); // Show newest first
    } catch (err) {
      console.error('Query error:', err);
      // Pass error to results view
      if (onQueryResult) {
        onQueryResult({ error: err.response?.data?.detail || 'Failed to process query' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = (historicalQuery) => {
    setQuery(historicalQuery);
  };

  const exampleQueries = [
    "How many employees do we have?",
    "Show me all Python developers", // Will hit document search
    "Average salary by department",
    "List employees hired in 2021"
  ];

  return (
    <div>
      <h2>Query Interface</h2>
      <form onSubmit={handleSubmit} className="mb-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Enter your question
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2"
            placeholder="Ask a question in natural language..."
            rows={3}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
        >
          {loading ? 'Processing...' : 'Submit Query'}
        </button>
      </form>
      
      <div>
        <p>Example queries:</p>
        <div>
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(example)}
              className="block w-full text-left px-3 py-2 bg-gray-100 hover:bg-gray-200"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {history.length > 0 && (
        <div>
          <p>Recent queries:</p>
          <div>
            {history.slice(0, 5).map((item, idx) => ( // Show 5 most recent
              <div
                key={idx}
                onClick={() => handleHistoryClick(item.query)}
                className="text-sm text-blue-600 hover:underline cursor-pointer"
                title={`Ran at: ${new Date(item.timestamp).toLocaleTimeString()}`}
              >
                {item.query}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QueryPanel;