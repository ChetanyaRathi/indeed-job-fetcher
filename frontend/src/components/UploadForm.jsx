import { useState, useRef } from 'react';

export default function UploadForm({ onSubmit, isLoading, seniority = 'any', onSeniorityChange }) {
  const [file, setFile] = useState(null);
  const [roles, setRoles] = useState('');
  const [location, setLocation] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf' || droppedFile.type === 'text/plain') {
        setFile(droppedFile);
      } else {
        alert('Please upload a PDF or TXT file.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a resume file first.');
      return;
    }
    
    onSubmit({ file, roles, location });
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div 
        className={`file-drop-area ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange}
          accept=".pdf,.txt"
        />
        {file ? (
          <p>Selected: <span className="selected-file">{file.name}</span></p>
        ) : (
          <p>Drag and drop your resume (PDF/TXT) here, or click to browse</p>
        )}
      </div>
      
      <div className="form-group">
        <label htmlFor="roles">Target Roles (comma-separated)</label>
        <input 
          type="text" 
          id="roles" 
          value={roles} 
          onChange={(e) => setRoles(e.target.value)} 
          placeholder="e.g. Backend Engineer, Python Developer"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="location">Location (optional)</label>
        <input 
          type="text" 
          id="location" 
          value={location} 
          onChange={(e) => setLocation(e.target.value)} 
          placeholder="e.g. Remote, New York, San Francisco"
        />
      </div>

      <div className="form-group">
        <label>Experience Level</label>
        <div className="seniority-options" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {[['any', 'All levels'], ['entry', 'Entry level'], ['mid', 'Mid level'], ['senior', 'Senior level']].map(([s, label]) => (
            <button
              type="button"
              key={s}
              onClick={() => onSeniorityChange && onSeniorityChange(s)}
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
      
      <button type="submit" className="btn-submit" disabled={isLoading || !file}>
        {isLoading ? 'Processing...' : 'Find Matches'}
      </button>
    </form>
  );
}
