import { useState, useEffect } from 'react';
import UploadForm from './components/UploadForm';
import JobCard from './components/JobCard';
import Loading from './components/Loading';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check health on load
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealthStatus(data))
      .catch(err => console.error("Could not fetch health:", err));
  }, []);

  const handleMatch = async ({ file, roles, location }) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('roles', roles);
    formData.append('location', location);
    
    try {
      const response = await fetch('/match', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch matches');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Indeed Job Fetcher</h1>
        <p>Private, local, LLM-powered job matching</p>
        
        {healthStatus && (
          <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Live Job Corpus: {healthStatus.corpus_size} roles loaded
          </div>
        )}
      </header>
      
      <UploadForm onSubmit={handleMatch} isLoading={isLoading} />
      
      {error && (
        <div className="error-alert">
          {error}
        </div>
      )}
      
      {isLoading && <Loading />}
      
      {results && !isLoading && (
        <div className="results-container">
          <div className="results-header">
            Ranked {results.count} matches from {results.corpus_size} relevant roles
          </div>
          
          {results.results.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No matches found with your criteria. Try adjusting your target roles.
            </div>
          ) : (
            <div className="job-list">
              {results.results.map((job, index) => (
                <JobCard key={index} job={job} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
