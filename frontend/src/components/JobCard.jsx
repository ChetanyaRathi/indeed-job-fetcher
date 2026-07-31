export default function JobCard({ job }) {
  const {
    title,
    company,
    location,
    salary,
    apply_url,
    fit_score,
    matched_skills,
    missing_skills,
    reason
  } = job;

  return (
    <div className="job-card">
      <div className="job-card-header">
        <div className="job-title-group">
          <h2>{title}</h2>
          <div>
            <span className="job-company">{company}</span>
            {location && <span className="job-location">• {location}</span>}
          </div>
        </div>
        <div className="fit-badge">
          {fit_score}% Fit
        </div>
      </div>

      <div className="job-details">
        {salary && <span className="detail-tag">{salary}</span>}
      </div>

      <div className="job-reason">
        <p>{reason}</p>
      </div>

      <div className="skills-section">
        <div className="skills-list">
          <h4>Matched Skills</h4>
          <div>
            {matched_skills && matched_skills.length > 0 ? (
              matched_skills.map((skill, i) => (
                <span key={i} className="skill-tag skill-matched">{skill}</span>
              ))
            ) : (
              <span className="text-muted">None explicitly mentioned</span>
            )}
          </div>
        </div>
        <div className="skills-list">
          <h4>Missing Skills</h4>
          <div>
            {missing_skills && missing_skills.length > 0 ? (
              missing_skills.map((skill, i) => (
                <span key={i} className="skill-tag skill-missing">{skill}</span>
              ))
            ) : (
              <span className="text-muted">None missing!</span>
            )}
          </div>
        </div>
      </div>

      {apply_url && (
        <a href={apply_url} target="_blank" rel="noopener noreferrer" className="apply-btn">
          Apply Now
        </a>
      )}
    </div>
  );
}
