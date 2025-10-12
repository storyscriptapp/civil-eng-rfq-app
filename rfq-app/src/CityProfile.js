import React, { useState, useEffect } from 'react';
import './CityProfile.css';
import API_BASE_URL from './config';

function CityProfile({ cityName, onBack, onViewJobs }) {
  const [cityData, setCityData] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    fetchCityProfile();
    fetchCityJobs();
  }, [cityName]);

  const fetchCityProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/city_profile/${encodeURIComponent(cityName)}`);
      const data = await response.json();
      setCityData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching city profile:', error);
      setLoading(false);
    }
  };

  const fetchCityJobs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rfqs`);
      const allJobs = await response.json();
      // Filter jobs for this city
      const cityJobs = allJobs.filter(job => job.organization === cityName);
      setJobs(cityJobs);
    } catch (error) {
      console.error('Error fetching city jobs:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading city profile...</div>;
  }

  if (!cityData) {
    return <div className="error">City not found</div>;
  }

  return (
    <div className="city-profile-container">
      <div className="profile-header">
        <button onClick={onBack} className="back-button">← Back to Cities</button>
        <h1>{cityData.name}</h1>
        <button onClick={() => onViewJobs(cityName)} className="view-jobs-button">
          View Jobs ({cityData.job_count || 0})
        </button>
      </div>

      <div className="profile-grid">
        {/* Scraping Configuration */}
        <div className="profile-card">
          <h2>Scraping Configuration</h2>
          <div className="config-item">
            <label>Status:</label>
            <span className={`status-badge ${cityData.is_active ? 'active' : 'inactive'}`}>
              {cityData.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div className="config-item">
            <label>URL:</label>
            <a href={cityData.url} target="_blank" rel="noopener noreferrer">
              {cityData.url}
            </a>
          </div>
          <div className="config-item">
            <label>Frequency:</label>
            <span className="placeholder-data">Daily (placeholder)</span>
          </div>
          <div className="config-item">
            <label>Uses Cloudflare:</label>
            <span>{cityData.uses_cloudflare ? 'Yes' : 'No'}</span>
          </div>
          <div className="config-item">
            <label>Dynamic Content:</label>
            <span>{cityData.is_dynamic ? 'Yes' : 'No'}</span>
          </div>
          <div className="config-item">
            <label>Has Pagination:</label>
            <span>{cityData.has_pagination ? 'Yes' : 'No'}</span>
          </div>
          {cityData.note && (
            <div className="config-note">
              <strong>Note:</strong> {cityData.note}
            </div>
          )}
        </div>

        {/* Scrape History */}
        <div className="profile-card">
          <h2>Recent Scrape History</h2>
          {cityData.scrape_history && cityData.scrape_history.length > 0 ? (
            <div className="history-list">
              {cityData.scrape_history.map((scrape, index) => (
                <div key={index} className="history-item">
                  <div className="history-date">{scrape.date}</div>
                  <div className="history-details">
                    <span className="history-count">{scrape.count} RFQs</span>
                    <span className="history-status">{scrape.status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="placeholder-data">No scrape history available yet</p>
          )}
        </div>

        {/* Demographics */}
        <div className="profile-card">
          <h2>Demographics</h2>
          <div className="demo-item">
            <label>Population (2025):</label>
            <span className="placeholder-data">{cityData.population_current || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Population (2020):</label>
            <span className="placeholder-data">{cityData.population_2020 || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Expected Growth:</label>
            <span className="placeholder-data">{cityData.expected_growth || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Avg. Household Income:</label>
            <span className="placeholder-data">
              {cityData.avg_household_income ? `$${cityData.avg_household_income.toLocaleString()}` : '—'}
            </span>
          </div>
          <div className="demo-item">
            <label>Drive Time from Tempe:</label>
            <span className="placeholder-data">{cityData.drive_time || '—'}</span>
          </div>
        </div>

        {/* Contact & Bonds */}
        <div className="profile-card">
          <h2>Contact & Bonds Information</h2>
          <div className="demo-item">
            <label>Primary Contact:</label>
            <span className="placeholder-data">{cityData.contact_name || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Contact Email:</label>
            <span className="placeholder-data">{cityData.contact_email || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Contact Phone:</label>
            <span className="placeholder-data">{cityData.contact_phone || '—'}</span>
          </div>
          <div className="demo-item">
            <label>Bonds (Upcoming Election):</label>
            <span className="placeholder-data">
              {cityData.bonds_upcoming !== null ? (cityData.bonds_upcoming ? 'Yes' : 'No') : '—'}
            </span>
          </div>
          <div className="demo-item">
            <label>Bonds (Last Election):</label>
            <span className="placeholder-data">
              {cityData.bonds_last !== null ? (cityData.bonds_last ? 'Yes' : 'No') : '—'}
            </span>
          </div>
          <div className="demo-item">
            <label>Bond Amount (Last):</label>
            <span className="placeholder-data">{cityData.bond_amount || '—'}</span>
          </div>
        </div>

        {/* Resources */}
        <div className="profile-card full-width">
          <h2>Resources & Links</h2>
          <div className="resources-grid">
            <div className="resource-item">
              <label>Master Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>Capital Improvement Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>Strategic Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>Annual Budget:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
          </div>
        </div>

        {/* Notes Section */}
        <div className="profile-card full-width">
          <h2>Internal Notes</h2>
          <textarea 
            className="notes-textarea" 
            placeholder="Add internal notes about this city/organization here..."
            value={cityData.internal_notes || ''}
            readOnly
          />
          <p className="placeholder-note">Note editing functionality coming soon!</p>
        </div>

        {/* Active RFQs/Jobs Section */}
        <div className="profile-card full-width">
          <h2>Active RFQs ({jobs.length})</h2>
          {jobs.length > 0 ? (
            <div className="jobs-table-container" style={{ overflowX: 'auto' }}>
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Job ID</th>
                    <th>RFP #</th>
                    <th>Title</th>
                    <th>Due Date</th>
                    <th>Work Type</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.job_id}>
                      <td>
                        {job.user_status === 'new' && <span className="badge bg-success">NEW</span>}
                        {job.user_status === 'pursuing' && <span className="badge bg-warning">Pursuing</span>}
                        {job.user_status === 'watch' && <span className="badge bg-primary">Watch</span>}
                        {job.user_status === 'completed' && <span className="badge bg-info">Completed</span>}
                        {job.user_status === 'lost' && <span className="badge bg-dark">Lost</span>}
                        {job.user_status === 'declined' && <span className="badge bg-secondary">Declined</span>}
                        {job.user_status === 'ignore' && <span className="badge bg-danger">Ignored</span>}
                      </td>
                      <td>
                        <small className="font-monospace">{job.job_id ? job.job_id.substring(0, 8) : 'N/A'}</small>
                      </td>
                      <td><small>{job.rfp_number}</small></td>
                      <td>
                        <a href={job.link || '#'} target="_blank" rel="noopener noreferrer">
                          {job.title}
                        </a>
                      </td>
                      <td><small>{job.due_date}</small></td>
                      <td><small>{job.work_type}</small></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted">No active RFQs for this city</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default CityProfile;

