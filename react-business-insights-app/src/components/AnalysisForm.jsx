import React, { useState, useEffect } from 'react';
import { fetchAnalysis } from '../services/api';
import ResultsDisplay from './ResultsDisplay';

const AnalysisForm = () => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [results, setResults] = useState(null);
    const [schema, setSchema] = useState(null); // State for schema

    let isMounted = true;

    useEffect(() => {
        return () => {
            isMounted = false; // Cleanup when the component unmounts
        };
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetchAnalysis(query);
            if (isMounted) {
                console.log('API Response:', response); // Debugging line
                setResults(response.analysis); // Set analysis results
                setSchema(response.schema); // Set schema details
            }
        } catch (err) {
            if (isMounted) {
                setError('An error occurred while fetching the analysis.');
            }
        } finally {
            if (isMounted) {
                setLoading(false);
            }
        }
    };

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
            {/* Logo Section */}
            <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#0078d4', marginBottom: '20px' }}>
                Business Insights Analyzer
            </h1>

            {/* Form Section */}
            <form onSubmit={handleSubmit} style={{ marginBottom: '20px', textAlign: 'left' }}>
                <div style={{ marginBottom: '15px' }}>
                    <label htmlFor="query" style={{ display: 'block', fontWeight: 'bold', marginBottom: '10px', fontSize: '16px', color: '#333' }}>
                        Enter your analysis query:
                    </label>
                    <textarea
                        id="query"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        required
                        rows="5"
                        style={{
                            width: '60%',
                            padding: '10px',
                            borderRadius: '4px',
                            border: '1px solid #ccc',
                            fontSize: '14px',
                            fontFamily: 'Arial, sans-serif',
                        }}
                    />
                </div>
                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        backgroundColor: loading ? '#ccc' : '#0078d4',
                        color: '#fff',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '4px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: '16px',
                    }}
                >
                    {loading ? 'Analyzing...' : 'Analyze'}
                </button>
                {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
            </form>

            {/* Results Section */}
            {results && <ResultsDisplay results={results} dbSchema={schema} />}
        </div>
    );
};

export default AnalysisForm;