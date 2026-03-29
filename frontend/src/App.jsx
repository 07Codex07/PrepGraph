import React, { useState, useEffect } from 'react';
import './App.css';
import CustomComponent from './components/CustomComponent';

function App() {
    const [data, setData] = useState([]);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/data');
                if (!response.ok) throw new Error('Network response was not ok');
                const result = await response.json();
                setData(result);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const renderContent = () => {
        if (isLoading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;
        if (data.length === 0) return <div>No data available.</div>;
        return data.map(item => <CustomComponent key={item.id} item={item} />);
    };

    return (
        <div className="app">
            <h1>My App</h1>
            <div className="timestamp">Last Updated: {new Date().toISOString()}</div>
            <div className="content">
                {renderContent()}
            </div>
        </div>
    );
}

export default App;