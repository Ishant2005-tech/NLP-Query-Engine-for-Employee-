import React, { useState, useEffect } from 'react';
import { getSchema } from '../services/api';

function SchemaVisualization() {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const loadSchema = async () => {
    setLoading(true);
    try {
      const data = await getSchema();
      setSchema(data);
    } catch (err) {
      console.error('Schema load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchema();
  }, []);

  if (loading) {
    return <div>Loading schema...</div>;
  }

  if (!schema) {
    return (
      <div>
        <h2>Database Schema</h2>
        <p>No schema available. Connect to database first.</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Database Schema</h2>
      <div>
        <div>
          <p>{schema.summary.total_tables}</p>
          <p>Tables</p>
        </div>
        <div>
          <p>{schema.summary.total_columns}</p>
          <p>Columns</p>
        </div>
        <div>
          <p>{schema.summary.total_relationships}</p>
          <p>Relationships</p>
        </div>
      </div>
      <div>
        {schema.tables.map((table, idx) => (
          <div key={idx} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
            <h3>{table.name}</h3>
            <p><em>{table.purpose}</em></p>
            <div>
              {table.columns.map((col, colIdx) => (
                <div key={colIdx} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>{col.name}</span>
                  <span>{col.type}</span>
                </div>
              ))}
            </div>
            {/* Removed PK part as our simple backend doesn't provide it */}
          </div>
        ))}
      </div>
      {schema.relationships.length > 0 && (
        <div>
          <h3>Relationships</h3>
          <div>
            {schema.relationships.map((rel, idx) => (
              <p key={idx}>
                {rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SchemaVisualization;