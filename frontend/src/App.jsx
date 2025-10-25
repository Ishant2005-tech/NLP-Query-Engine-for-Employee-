import React, { useState } from 'react';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';
import SchemaVisualization from './components/SchemaVisualization';

function App() {
  const [connected, setConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('connect');
  const [queryResult, setQueryResult] = useState(null);

  const handleConnectionSuccess = () => {
    setConnected(true);
    setActiveTab('query');
  };

  return (
    <div>
      <nav className="bg-white shadow-md">
        <div>
          <h1>NLP Query Engine</h1>
          <p>Natural Language Interface for Employee Database</p>
        </div>
      </nav>
      <div>
        <div>
          <button
            onClick={() => setActiveTab('connect')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'connect'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            Connect Data
          </button>
          <button
            onClick={() => setActiveTab('query')}
            disabled={!connected}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'query'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            } disabled:opacity-50`}
          >
            Query Data
          </button>
          <button
            onClick={() => setActiveTab('schema')}
            disabled={!connected}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'schema'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            } disabled:opacity-50`}
          >
            View Schema
          </button>
        </div>
        {activeTab === 'connect' && (
          <div>
            <DatabaseConnector onConnectionSuccess={handleConnectionSuccess} />
            <DocumentUploader />
          </div>
        )}
        {activeTab === 'query' && (
          <div>
            <div>
              <QueryPanel onQueryResult={setQueryResult} />
            </div>
            <div>
              <ResultsView result={queryResult} />
            </div>
          </div>
        )}
        {activeTab === 'schema' && <SchemaVisualization />}
      </div>
    </div>
  );
}

export default App;