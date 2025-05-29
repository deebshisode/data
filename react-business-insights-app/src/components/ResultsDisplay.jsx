import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const ResultsDisplay = ({ results, dbSchema }) => {
    const [showFullSuggestions, setShowFullSuggestions] = useState(false);

    if (!results) {
        return <div>No results to display.</div>;
    }

    const maxLines = 5; // Maximum number of lines to display initially
    const aiSuggestionsLines = results.aiSuggestions.split('\n');

    return (
        <div style={{ display: 'flex', gap: '20px', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            {/* Left Section: Analysis Results */}
            <div style={{ flex: 2, padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)' }}>
                <h2 style={{ borderBottom: '2px solid #0078d4', paddingBottom: '10px' }}>Analysis Results</h2>
                <h3>Goal:</h3>
                <p>{results.goal}</p>
                <h4 style={{ fontSize: '16px', marginBottom: '10px' }}>AI Suggestions:</h4>
                <div style={{ 
                    backgroundColor: '#f4f4f4', 
                    padding: '10px', 
                    borderRadius: '4px', 
                    overflowX: 'auto', 
                    whiteSpace: 'pre-wrap', 
                    fontSize: '13px', 
                    lineHeight: '1.5', 
                    color: '#333' 
                }}>
                    {(showFullSuggestions ? aiSuggestionsLines : aiSuggestionsLines.slice(0, maxLines)).map((line, index) => (
                        <p key={index} style={{ margin: '5px 0' }}>
                            {line}
                        </p>
                    ))}
                    {aiSuggestionsLines.length > maxLines && (
                        <button
                            onClick={() => setShowFullSuggestions(!showFullSuggestions)}
                            style={{
                                marginTop: '10px',
                                backgroundColor: '#0078d4',
                                color: '#fff',
                                border: 'none',
                                padding: '5px 10px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px',
                            }}
                        >
                            {showFullSuggestions ? 'Show Less' : 'Show More'}
                        </button>
                    )}
                </div>
                <h4>Suggested SQL Queries:</h4>
                <ul style={{ listStyleType: 'disc', paddingLeft: '20px' }}>
                    {results.suggestedQueries &&
                        results.suggestedQueries.map((query, index) => (
                            <li key={index} style={{ marginBottom: '10px' }}>
                                <pre style={{ backgroundColor: '#f4f4f4', padding: '10px', borderRadius: '4px', overflowX: 'auto' }}>{query}</pre>
                            </li>
                        ))}
                </ul>
                <h4>Query Results:</h4>
                {results.results &&
                    Object.entries(results.results).map(([queryKey, queryResult]) => (
                        <div key={queryKey} style={{ marginBottom: '20px' }}>
                            <h5>{queryKey}:</h5>
                            <pre style={{ backgroundColor: '#f4f4f4', padding: '10px', borderRadius: '4px', overflowX: 'auto' }}>{queryResult.sql}</pre>
                            {queryResult.error ? (
                                <p style={{ color: 'red' }}>Error: {queryResult.error}</p>
                            ) : (
                                <div>
                                    <h6>Results:</h6>
                                    <table border="1" style={{ borderCollapse: 'collapse', width: '100%', marginTop: '10px' }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#0078d4', color: '#fff' }}>
                                                {queryResult.results.length > 0 &&
                                                    Object.keys(queryResult.results[0]).map((column, index) => (
                                                        <th key={index} style={{ padding: '10px', textAlign: 'left' }}>
                                                            {column}
                                                        </th>
                                                    ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {queryResult.results.map((row, rowIndex) => (
                                                <tr key={rowIndex} style={{ backgroundColor: rowIndex % 2 === 0 ? '#f9f9f9' : '#fff' }}>
                                                    {Object.values(row).map((value, colIndex) => (
                                                        <td key={colIndex} style={{ padding: '10px' }}>
                                                            {value}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    ))}
            </div>

            {/* Right Section: Database Schema */}
            <div style={{ flex: 1, borderLeft: '1px solid #ccc', paddingLeft: '20px', maxHeight: '500px', overflowY: 'auto', backgroundColor: '#f9f9f9', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)' }}>
                <h3 style={{ borderBottom: '2px solid #0078d4', paddingBottom: '10px' }}>Database Schema</h3>
                {dbSchema && Object.entries(dbSchema).length > 0 ? (
                    <ul style={{ listStyleType: 'none', paddingLeft: '0' }}>
                        {Object.entries(dbSchema).map(([tableName, tableDetails], index) => (
                            <li key={index} style={{ marginBottom: '20px' }}>
                                <strong style={{ color: '#0078d4' }}>{tableName}</strong>
                                <ul style={{ listStyleType: 'circle', paddingLeft: '20px' }}>
                                    <li>
                                        <strong>Columns:</strong>
                                        <ul style={{ listStyleType: 'square', paddingLeft: '20px' }}>
                                            {tableDetails.columns.map((column, colIndex) => (
                                                <li key={colIndex}>
                                                    {column.name} ({column.type}){' '}
                                                    {column.nullable ? '(Nullable)' : '(Not Nullable)'}
                                                </li>
                                            ))}
                                        </ul>
                                    </li>
                                    {tableDetails.relationships && tableDetails.relationships.length > 0 && (
                                        <li>
                                            <strong>Relationships:</strong>
                                            <ul style={{ listStyleType: 'square', paddingLeft: '20px' }}>
                                                {tableDetails.relationships.map((relationship, relIndex) => (
                                                    <li key={relIndex}>
                                                        {relationship.column} → {relationship.references.table} (
                                                        {relationship.references.column})
                                                    </li>
                                                ))}
                                            </ul>
                                        </li>
                                    )}
                                </ul>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>No schema details available.</p>
                )}
            </div>
        </div>
    );
};

export default ResultsDisplay;