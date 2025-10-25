import React, { useState } from 'react';
import { connectDatabase } from '../services/api';

function DatabaseConnector({ onConnectionSuccess }) {
  // Changed default to our SQLite DB
  const [connectionString, setConnectionString] = useState(
    'sqlite+aiosqlite:///./employee.db'
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      // Use a dummy string for SQLite, as the backend uses the .env file
      const dummyConnectionString = 'sqlite+aiosqlite:///./employee.db';
      const result = await connectDatabase(dummyConnectionString);
      setSuccess(`Connected! Found ${result.schema_summary.total_tables} tables`);
      if (onConnectionSuccess) {
        onConnectionSuccess(result);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Database Connection</h2>
      <div>
        <label className="block text-sm font-medium mb-2">
          Connection String
        </label>
        <input
          type="text"
          value={connectionString}
          onChange={(e) => setConnectionString(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2"
          placeholder="sqlite+aiosqlite:///./employee.db"
          readOnly // Make it read-only since we use the .env config
        />
      </div>
      <button
        onClick={handleConnect}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
      >
        {loading ? 'Connecting...' : 'Connect & Analyze'}
      </button>
      {error && (
        <div>
          {error}
        </div>
      )}
      {success && (
        <div>
          {success}
        </div>
      )}
    </div>
  );
}

export default DatabaseConnector;