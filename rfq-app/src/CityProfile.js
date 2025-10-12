import React, { useState, useEffect } from 'react';
import './CityProfile.css';
import API_BASE_URL from './config';

function CityProfile({ cityName, onBack, onViewJobs }) {
  const [cityData, setCityData] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  
  // Filters for jobs list
  const [filters, setFilters] = useState({
    workType: 'all',
    userStatus: 'all',
    hideIgnored: true,
    sortBy: 'due_date'
  });

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

  // Helper function for date parsing
  const parseDateSafely = (dateStr) => {
    if (!dateStr || dateStr === 'N/A') return null;
    try {
      let cleanedDate = dateStr
        .replace(/(\d+)(st|nd|rd|th)/g, '$1')
        .replace(/\s+MST|\s+PST|\s+EST|\s+CST/gi, '')
        .trim();
      const date = new Date(cleanedDate);
      return isNaN(date.getTime()) ? null : date;
    } catch {
      return null;
    }
  };

  // Helper function for due date styling
  const getDueDateStyle = (dueDateStr) => {
    const dueDate = parseDateSafely(dueDateStr);
    if (!dueDate) return {};
    
    const now = new Date();
    const diffDays = (dueDate - now) / (1000 * 60 * 60 * 24);
    
    if (diffDays < 0) return { color: 'red', fontWeight: 'bold' };
    if (diffDays <= 7) return { color: 'darkorange', fontWeight: 'bold' };
    if (diffDays <= 14) return { color: 'orange' };
    return {};
  };

  // Filter and sort jobs
  const filteredJobs = jobs.filter(job => {
    if (filters.workType !== 'all' && job.work_type !== filters.workType) return false;
    if (filters.userStatus !== 'all' && job.user_status !== filters.userStatus) return false;
    if (filters.hideIgnored && job.user_status === 'ignore') return false;
    return true;
  }).sort((a, b) => {
    switch (filters.sortBy) {
      case 'due_date':
        const dateA = parseDateSafely(a.due_date);
        const dateB = parseDateSafely(b.due_date);
        const now = new Date();
        if (!dateA && !dateB) return 0;
        if (!dateA) return 1;
        if (!dateB) return -1;
        const futureA = dateA >= now;
        const futureB = dateB >= now;
        if (futureA && !futureB) return -1;
        if (!futureA && futureB) return 1;
        return dateA - dateB;
      case 'work_type':
        return (a.work_type || '').localeCompare(b.work_type || '');
      case 'date_added':
        const addedA = a.first_seen ? new Date(a.first_seen) : new Date(0);
        const addedB = b.first_seen ? new Date(b.first_seen) : new Date(0);
        return addedB - addedA;
      default:
        return 0;
    }
  });

  if (loading) {
    return <div className="loading">Loading city profile...</div>;
  }

  if (!cityData) {
    return <div className="error">City not found</div>;
  }

  // Check if this is a manual-only city
  const isManualOnly = cityData.manual || !cityData.is_active;

  return (
    <div className="city-profile-container">
      <div className="profile-header">
        <button onClick={onBack} className="back-button">← Back to Cities</button>
        <h1>{cityData.name}</h1>
      </div>

      <div className="profile-grid">
        {/* 1. Manual Entry Alert (if required) */}
        {isManualOnly && (
          <div className="profile-card full-width" style={{ backgroundColor: '#fff3cd', borderColor: '#ffc107' }}>
            <h2 style={{ color: '#856404' }}>⚠️ Manual Entry Required</h2>
            <p style={{ color: '#856404', marginBottom: 0 }}>
              This city requires manual job entry. Please check their procurement website directly and use the "Add Job Manually" section below to add new opportunities.
            </p>
          </div>
        )}

        {/* 2. Active RFQs with Filters */}
        <div className="profile-card full-width">
          <h2>Active RFQs ({filteredJobs.length})</h2>
          
          {/* Filters */}
          <div className="row mb-3">
            <div className="col-md-3">
              <label className="form-label">Work Type</label>
              <select 
                className="form-select form-select-sm"
                value={filters.workType}
                onChange={e => setFilters({...filters, workType: e.target.value})}
              >
                <option value="all">All Types</option>
                <option value="Civil">Civil</option>
                <option value="Construction">Construction</option>
                <option value="CMAR">CMAR</option>
                <option value="Utility/Transportation">Utility/Transportation</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Status</label>
              <select 
                className="form-select form-select-sm"
                value={filters.userStatus}
                onChange={e => setFilters({...filters, userStatus: e.target.value})}
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="pursuing">Pursuing</option>
                <option value="watch">Watch</option>
                <option value="completed">Completed</option>
                <option value="lost">Lost</option>
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Sort By</label>
              <select 
                className="form-select form-select-sm"
                value={filters.sortBy}
                onChange={e => setFilters({...filters, sortBy: e.target.value})}
              >
                <option value="due_date">Due Date</option>
                <option value="work_type">Work Type</option>
                <option value="date_added">Date Added</option>
              </select>
            </div>
            <div className="col-md-3">
              <div className="form-check" style={{ marginTop: '32px' }}>
                <input 
                  className="form-check-input"
                  type="checkbox"
                  checked={filters.hideIgnored}
                  onChange={e => setFilters({...filters, hideIgnored: e.target.checked})}
                  id="hideIgnoredCity"
                />
                <label className="form-check-label" htmlFor="hideIgnoredCity">
                  Hide Ignored
                </label>
              </div>
            </div>
          </div>

          {/* Jobs Table */}
          {filteredJobs.length > 0 ? (
            <div className="jobs-table-container" style={{ overflowX: 'auto' }}>
              <table className="table table-hover table-sm">
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
                  {filteredJobs.map((job) => (
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
                      <td style={getDueDateStyle(job.due_date)}><small>{job.due_date}</small></td>
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

        {/* 3. Internal Notes */}
        <div className="profile-card full-width">
          <h2>Internal Notes</h2>
          <textarea 
            className="notes-textarea" 
            placeholder="Add internal notes about this city/organization here..."
            value={cityData.internal_notes || ''}
            readOnly
            style={{ width: '100%', minHeight: '120px', padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}
          />
          <p className="placeholder-note">Note editing functionality coming soon!</p>
        </div>

        {/* 4. Uploaded Documents */}
        <div className="profile-card full-width">
          <h2>Documents & Resources</h2>
          <div className="resources-grid">
            <div className="resource-item">
              <label>📄 Master Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>📄 Capital Improvement Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>📄 Strategic Plan:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
            <div className="resource-item">
              <label>📄 Annual Budget:</label>
              <span className="placeholder-data">Not added yet</span>
            </div>
          </div>
          <p className="placeholder-note">Document upload functionality coming soon!</p>
        </div>

        {/* 5. Add Job Manually */}
        <div className="profile-card full-width">
          <h2>Add Job Manually</h2>
          <p className="text-muted">Use this section to manually add jobs from this city's procurement website.</p>
          <button className="btn btn-primary" disabled>
            ➕ Add Job (Coming Soon)
          </button>
          <p className="placeholder-note" style={{ marginTop: '10px' }}>
            This will allow you to paste job information or enter it manually, similar to the parsing tool on the main RFQ page.
          </p>
        </div>

        {/* 6. Scraping Configuration & History */}
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

        {/* 7. Demographics */}
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

        {/* 8. Contact & Bonds */}
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
      </div>
    </div>
  );
}

export default CityProfile;
