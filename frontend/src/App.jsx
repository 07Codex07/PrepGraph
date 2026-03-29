import React from 'react';
import './App.css';

function App() {
  const [error, setError] = React.useState(null);

  const handleError = (message) => {
    setError(message);
    // Add custom animation or transition here
  };

  const handleAction = () => {
    // Example action to trigger error handling
    // handleError('Some error occurred!');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">Welcome to PrepGraph</h1>
      </header>
      <main className="app-main">
        <button className="app-button" onClick={handleAction}>Click Me</button>
        {error && <div className="error-message fade-in">{error}</div>}
      </main>
    </div>
  );
}

export default App;
