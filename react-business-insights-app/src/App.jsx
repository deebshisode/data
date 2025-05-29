import React, { useState } from 'react';
import AnalysisForm from './components/AnalysisForm';
import ResultsDisplay from './components/ResultsDisplay';
import { fetchAnalysis } from './services/api';

const App = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleQueryChange = (event) => {
        setQuery(event.target.value);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const response = await fetchAnalysis(query);
            setResults(response.data);
        } catch (err) {
            setError('Error fetching analysis results. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <AnalysisForm query={query} onQueryChange={handleQueryChange} onSubmit={handleSubmit} />
            {loading && <p>Loading...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {results && <ResultsDisplay results={results} />}
        </div>
    );
};

export default App;