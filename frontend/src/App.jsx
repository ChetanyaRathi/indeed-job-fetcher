import { useState, useEffect } from 'react';
import UploadForm from './components/UploadForm';
import JobCard from './components/JobCard';
import Loading from './components/Loading';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  
  const [window, setWindow] = useState('1w');
  const [seniority, setSeniority] = useState('any');
  const [lastQuery, setLastQuery] = useState(null);

  useEffect(() => {
    // Check health on load
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealthStatus(data))
      .catch(err => console.error("Could not fetch health:", err));
  }, []);

  const handleMatch = async (queryOverrides = {}) => {
    const currentQuery = { ...lastQuery, ...queryOverrides };
    if (!currentQuery.file) return;

    setIsLoading(true);
    setError(null);
    setResults(null);
    setLastQuery(currentQuery);

    const formData = new FormData();
    formData.append('resume', currentQuery.file);
    formData.append('roles', currentQuery.roles || '');
    formData.append('location', currentQuery.location || '');
    formData.append('window', currentQuery.window || window);
    formData.append('seniority', currentQuery.seniority || seniority);
    
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

  const handleInitialSubmit = ({ file, roles, location }) => {
    handleMatch({ file, roles, location, window, seniority });
  };

  const handleWindowChange = (newWindow) => {
    setWindow(newWindow);
    if (lastQuery) {
      handleMatch({ window: newWindow });
    }
  };

  const handleSeniorityChange = (newSeniority) => {
    setSeniority(newSeniority);
    if (lastQuery) {
      handleMatch({ seniority: newSeniority });
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
      
      <UploadForm
        onSubmit={handleInitialSubmit}
        isLoading={isLoading}
        seniority={seniority}
        onSeniorityChange={setSeniority}
      />
      
      {error && (
        <div className="error-alert">
          {error}
        </div>
      )}
      
      {isLoading && <Loading />}
      
      {results && !isLoading && (
        <div className="results-container">
          <div className="filters-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem', padding: '1rem', backgroundColor: 'var(--surface-color)', borderRadius: 'var(--border-radius)' }}>
            <div className="date-tabs" style={{ display: 'flex', gap: '0.5rem' }}>
              {['1d', '3d', '1w'].map(w => (
                <button 
                  key={w}
                  onClick={() => handleWindowChange(w)}
                  style={{
                    padding: '0.5rem 1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--border-radius)',
                    backgroundColor: window === w ? 'var(--primary-color)' : 'transparent',
                    color: window === w ? 'white' : 'inherit',
                    cursor: 'pointer'
                  }}
                >
                  Past {w === '1d' ? '1 day' : w === '3d' ? '3 days' : '1 week'}
                </button>
              ))}
            </div>
            <div className="seniority-tabs" style={{ display: 'flex', gap: '0.5rem' }}>
              {[['any', 'All levels'], ['entry', 'Entry'], ['mid', 'Mid'], ['senior', 'Senior']].map(([s, label]) => (
                <button
                  key={s}
                  onClick={() => handleSeniorityChange(s)}
                  style={{
                    padding: '0.5rem 1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--border-radius)',
                    backgroundColor: seniority === s ? 'var(--primary-color)' : 'transparent',
                    color: seniority === s ? 'white' : 'inherit',
                    cursor: 'pointer'
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="results-header">
            Ranked {results.count} matches from {results.corpus_size} relevant roles
          </div>
          
          {results.results.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No matches found with your criteria. Try adjusting your target roles or filters.
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
