import React, { useEffect, useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import JobDetails from './JobDetails';
import CitiesList from './CitiesList';
import CityProfile from './CityProfile';
import Login from './Login';

function App() {
    const [auth, setAuth] = useState(localStorage.getItem('auth') || null);
    const [rfqs, setRfqs] = useState([]);
    const [cities, setCities] = useState([]);
    const [newCity, setNewCity] = useState({ organization: '', url: '', row_selector: '', cell_count: 4, is_dynamic: false, manual: false });
    const [pasteText, setPasteText] = useState('');
    const [pasteUrl, setPasteUrl] = useState('');
    const [screenshot, setScreenshot] = useState(null);
    const [screenshotOrg, setScreenshotOrg] = useState('');
    
    // Filter states
    const [filters, setFilters] = useState({
        workType: 'all',
        userStatus: 'all',
        organization: 'all',
        searchTerm: '',
        hideIgnored: true  // Hide ignored by default
    });
    
    // Selected job for detail view
    const [selectedJobId, setSelectedJobId] = useState(null);
    const [currentView, setCurrentView] = useState('rfqs'); // 'rfqs', 'cities', 'city-profile'
    const [selectedCity, setSelectedCity] = useState(null);
    const [healthData, setHealthData] = useState(null);

    useEffect(() => {
        fetch('http://localhost:8000/rfqs')
            .then(res => res.json())
            .then(data => {
                console.log('RFQs:', data);
                setRfqs(data);
            })
            .catch(err => console.error('Error fetching RFQs:', err));
        fetch('/rfq_scraper/cities.json')
            .then(res => res.json())
            .then(data => setCities(data))
            .catch(err => console.error('Error fetching cities:', err));
        // Fetch health data
        fetch('http://localhost:8000/health')
            .then(res => res.json())
            .then(data => {
                console.log('Health data:', data);
                setHealthData(data);
            })
            .catch(err => console.error('Error fetching health data:', err));
    }, []);

    const addCity = () => {
        setCities([...cities, newCity]);
        fetch('http://localhost:8000/save_cities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify([...cities, newCity])
        })
            .then(res => res.json())
            .then(data => console.log('City saved:', data))
            .catch(err => console.error('Error saving city:', err));
    };

    const runScraper = () => {
        fetch('http://localhost:8000/run_scraper', { 
            method: 'POST',
            headers: {
                'Authorization': `Basic ${auth}`
            }
        })
            .then(res => res.json())
            .then(data => console.log('Scraper:', data))
            .catch(err => console.error('Error running scraper:', err));
    };

    const handleLogout = () => {
        localStorage.removeItem('auth');
        setAuth(null);
    };

    const parseText = () => {
        if (!screenshotOrg || !pasteText.trim()) {
            alert('Please enter both organization name and text to parse');
            return;
        }
        
        fetch('http://localhost:8000/parse_text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: pasteText, 
                organization: screenshotOrg,
                url: pasteUrl.trim() || ''
            })
        })
            .then(res => res.json())
            .then(data => {
                console.log('Parse result:', data);
                if (data.rfqs && data.rfqs.length > 0) {
                    alert(`✅ Successfully parsed and saved ${data.rfqs.length} job(s)!`);
                    // Reload RFQs from database to get complete data with job_id
                    fetchRfqs();
                    // Clear the input fields
                    setPasteText('');
                    setPasteUrl('');
                } else {
                    alert('⚠️ Could not parse any jobs from the text. Check the format and try again.');
                }
            })
            .catch(err => {
                console.error('Error parsing text:', err);
                alert('❌ Error parsing text. Check console for details.');
            });
    };

    const uploadScreenshot = () => {
        const formData = new FormData();
        formData.append('file', screenshot);
        formData.append('organization', screenshotOrg);
        fetch('http://localhost:8000/upload_screenshot', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                setRfqs([...rfqs, ...data.rfqs]);
                console.log('Screenshot RFQs:', data);
            })
            .catch(err => console.error('Error uploading screenshot:', err));
    };

    const updateUserStatus = (jobId, status, notes = null) => {
        fetch('http://localhost:8000/update_job_status', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Basic ${auth}`
            },
            body: JSON.stringify({ job_id: jobId, status, notes })
        })
            .then(res => res.json())
            .then(data => {
                // Update local state
                setRfqs(rfqs.map(rfq => 
                    rfq.job_id === jobId ? { ...rfq, user_status: status, user_notes: notes } : rfq
                ));
                console.log('Updated job status:', data);
            })
            .catch(err => console.error('Error updating job status:', err));
    };

    const updateWorkType = (jobId, workType) => {
        fetch('http://localhost:8000/update_work_type', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Basic ${auth}`
            },
            body: JSON.stringify({ job_id: jobId, work_type: workType })
        })
            .then(res => res.json())
            .then(data => {
                // Update local state
                setRfqs(rfqs.map(rfq => 
                    rfq.job_id === jobId ? { ...rfq, work_type: workType } : rfq
                ));
                console.log('Updated work type:', data);
            })
            .catch(err => console.error('Error updating work type:', err));
    };

    // Apply filters
    const filteredRfqs = rfqs.filter(rfq => {
        // Filter by work type
        if (filters.workType !== 'all' && rfq.work_type !== filters.workType) return false;
        
        // Filter by user status
        if (filters.userStatus !== 'all' && rfq.user_status !== filters.userStatus) return false;
        
        // Filter by organization
        if (filters.organization !== 'all' && rfq.organization !== filters.organization) return false;
        
        // Hide ignored jobs (if checked)
        if (filters.hideIgnored && rfq.user_status === 'ignore') return false;
        
        // Filter by search term
        if (filters.searchTerm) {
            const searchLower = filters.searchTerm.toLowerCase();
            const matchesSearch = 
                rfq.title?.toLowerCase().includes(searchLower) ||
                rfq.rfp_number?.toLowerCase().includes(searchLower) ||
                rfq.organization?.toLowerCase().includes(searchLower);
            if (!matchesSearch) return false;
        }
        
        return true;
    });

    // Get unique organizations for filter dropdown
    const organizations = [...new Set(rfqs.map(rfq => rfq.organization))].sort();

    // Navigation handlers
    const handleCitySelect = (cityName) => {
        setSelectedCity(cityName);
        setCurrentView('city-profile');
    };

    const handleViewJobs = (cityName) => {
        setCurrentView('rfqs');
        setFilters({
            ...filters,
            organization: cityName
        });
    };

    // If viewing a specific job, show the JobDetails component
    if (selectedJobId) {
        return <JobDetails jobId={selectedJobId} auth={auth} onBack={() => {
            setSelectedJobId(null);
            // Refresh RFQs list when returning
            fetch('http://localhost:8000/rfqs')
                .then(res => res.json())
                .then(data => setRfqs(data))
                .catch(err => console.error('Error fetching RFQs:', err));
        }} />;
    }

    // Show login screen if not authenticated
    if (!auth) {
        return <Login onLogin={setAuth} />;
    }

    // If viewing cities list
    if (currentView === 'cities') {
        return (
            <CitiesList 
                auth={auth}
                onCitySelect={handleCitySelect}
                onBack={() => setCurrentView('rfqs')}
            />
        );
    }

    // If viewing city profile
    if (currentView === 'city-profile' && selectedCity) {
        return (
            <CityProfile 
                cityName={selectedCity}
                onBack={() => setCurrentView('cities')}
                onViewJobs={handleViewJobs}
            />
        );
    }

    return (
        <div className="container mt-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h1>RFQ Tracker</h1>
                <div className="d-flex gap-2 align-items-center">
                    <button 
                        onClick={() => setCurrentView('cities')} 
                        className="btn btn-info"
                    >
                        📍 View Cities ({organizations.length})
                    </button>
                    <button className="btn btn-primary" onClick={runScraper}>
                        <i className="bi bi-arrow-clockwise"></i> Run Scraper
                    </button>
                    <button className="btn btn-outline-secondary" onClick={handleLogout} title="Logout">
                        🚪 Logout
                    </button>
                </div>
            </div>

            {/* Health Alerts */}
            {healthData && healthData.alerts && healthData.alerts.length > 0 && (
                <div className="alert-container mb-4">
                    {healthData.has_critical_alerts && (
                        <div className="alert alert-danger">
                            <h5 className="alert-heading">🚨 Critical Issues Detected</h5>
                            <ul className="mb-0">
                                {healthData.alerts.filter(a => a.severity === 'critical').map((alert, idx) => (
                                    <li key={idx}><strong>{alert.city}:</strong> {alert.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {healthData.has_warnings && !healthData.has_critical_alerts && (
                        <div className="alert alert-warning">
                            <h5 className="alert-heading">⚠️ Scraper Warnings</h5>
                            <ul className="mb-0">
                                {healthData.alerts.filter(a => a.severity === 'warning' || a.severity === 'error').map((alert, idx) => (
                                    <li key={idx}><strong>{alert.city}:</strong> {alert.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {healthData.timestamp && (
                        <div className="text-muted small">
                            Last scrape: {new Date(healthData.timestamp).toLocaleString()} | 
                            Cities: {healthData.cities_scraped} | 
                            Success: {healthData.success_count} | 
                            Failed: {healthData.failed_count}
                        </div>
                    )}
                </div>
            )}

            {/* Filters */}
            <div className="card mb-4">
                <div className="card-body">
                    <h5 className="card-title">Filters</h5>
                    <div className="row g-3">
                        <div className="col-md-3">
                            <label className="form-label">Search</label>
                            <input 
                                type="text" 
                                className="form-control" 
                                placeholder="Search title, number, org..."
                                value={filters.searchTerm}
                                onChange={e => setFilters({...filters, searchTerm: e.target.value})}
                            />
                        </div>
                        <div className="col-md-2">
                            <label className="form-label">Work Type</label>
                            <select 
                                className="form-select"
                                value={filters.workType}
                                onChange={e => setFilters({...filters, workType: e.target.value})}
                            >
                                <option value="all">All Types</option>
                                <option value="civil">Civil Engineering</option>
                                <option value="utility/transportation">Utility/Transportation</option>
                                <option value="maintenance">Maintenance</option>
                                <option value="architecture">Architecture</option>
                                <option value="mechanical">Mechanical</option>
                                <option value="electrical">Electrical</option>
                                <option value="environmental">Environmental</option>
                                <option value="it">IT/Technology</option>
                                <option value="other">Other</option>
                                <option value="unknown">Unknown</option>
                            </select>
                        </div>
                        <div className="col-md-2">
                            <label className="form-label">Status</label>
                            <select 
                                className="form-select"
                                value={filters.userStatus}
                                onChange={e => setFilters({...filters, userStatus: e.target.value})}
                            >
                                <option value="all">All Status</option>
                                <option value="new">New</option>
                                <option value="pursuing">Pursuing</option>
                                <option value="completed">Completed</option>
                                <option value="declined">Declined</option>
                                <option value="ignore">Ignored</option>
                            </select>
                        </div>
                        <div className="col-md-3">
                            <label className="form-label">Organization</label>
                            <select 
                                className="form-select"
                                value={filters.organization}
                                onChange={e => setFilters({...filters, organization: e.target.value})}
                            >
                                <option value="all">All Organizations</option>
                                {organizations.map(org => (
                                    <option key={org} value={org}>{org}</option>
                                ))}
                            </select>
                        </div>
                        <div className="col-md-2 d-flex align-items-end">
                            <div className="form-check">
                                <input 
                                    className="form-check-input" 
                                    type="checkbox" 
                                    id="hideIgnored"
                                    checked={filters.hideIgnored}
                                    onChange={e => setFilters({...filters, hideIgnored: e.target.checked})}
                                />
                                <label className="form-check-label" htmlFor="hideIgnored">
                                    Hide Ignored
                                </label>
                            </div>
                        </div>
                    </div>
                    <div className="mt-2">
                        <span className="text-muted">
                            Showing {filteredRfqs.length} of {rfqs.length} RFQs
                        </span>
                        {filteredRfqs.length !== rfqs.length && (
                            <button 
                                className="btn btn-sm btn-link" 
                                onClick={() => setFilters({workType: 'all', userStatus: 'all', organization: 'all', searchTerm: '', hideIgnored: false})}
                            >
                                Clear Filters
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* RFQs Table */}
            <div className="card">
                <div className="card-body">
                    <h5 className="card-title">RFQs</h5>
                    <div className="table-responsive">
                        <table className="table table-hover">
                <thead>
                    <tr>
                                    <th>Status</th>
                                    <th>Job ID</th>
                        <th>Organization</th>
                        <th>Title</th>
                        <th>Work Type</th>
                        <th>Due Date</th>
                                    <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                                {filteredRfqs.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="text-center text-muted">
                                            No RFQs match your filters
                                        </td>
                                    </tr>
                                ) : (
                                    filteredRfqs.map((rfq) => (
                                        <tr key={rfq.job_id || rfq.rfp_number} className={rfq.user_status === 'new' ? 'table-primary' : ''}>
                                            <td>
                                                {rfq.user_status === 'new' && <span className="badge bg-success">NEW</span>}
                                                {rfq.user_status === 'pursuing' && <span className="badge bg-warning">Pursuing</span>}
                                                {rfq.user_status === 'completed' && <span className="badge bg-info">Completed</span>}
                                                {rfq.user_status === 'declined' && <span className="badge bg-secondary">Declined</span>}
                                                {rfq.user_status === 'ignore' && <span className="badge bg-danger">Ignored</span>}
                                            </td>
                                            <td>
                                                <a
                                                    href="#"
                                                    className="font-monospace text-decoration-none"
                                                    title={`View details for ${rfq.job_id}`}
                                                    onClick={(e) => {
                                                        e.preventDefault();
                                                        setSelectedJobId(rfq.job_id);
                                                    }}
                                                >
                                                    {rfq.job_id ? rfq.job_id.substring(0, 8) : 'N/A'}
                                                </a>
                                            </td>
                                            <td><small>{rfq.organization}</small></td>
                                            <td>
                                                <a href={rfq.link || '#'} target="_blank" rel="noopener noreferrer">
                                                    {rfq.title}
                                                </a>
                                                <br />
                                                <small className="text-muted">Org #: {rfq.rfp_number}</small>
                                            </td>
                                            <td>
                                                <select 
                                                    className="form-select form-select-sm"
                                                    value={rfq.work_type || 'unknown'}
                                                    onChange={(e) => updateWorkType(rfq.job_id, e.target.value)}
                                                    style={{minWidth: '150px'}}
                                                >
                                                    <option value="civil">Civil Engineering</option>
                                                    <option value="utility/transportation">Utility/Transportation</option>
                                                    <option value="maintenance">Maintenance</option>
                                                    <option value="architecture">Architecture</option>
                                                    <option value="mechanical">Mechanical</option>
                                                    <option value="electrical">Electrical</option>
                                                    <option value="environmental">Environmental</option>
                                                    <option value="it">IT/Technology</option>
                                                    <option value="other">Other</option>
                                                    <option value="unknown">Unknown</option>
                                                </select>
                                            </td>
                            <td>{rfq.due_date}</td>
                                            <td>
                                                <div className="btn-group btn-group-sm" role="group">
                                                    <button 
                                                        className="btn btn-outline-success" 
                                                        onClick={() => updateUserStatus(rfq.job_id, 'pursuing')}
                                                        title="Mark as Pursuing"
                                                    >
                                                        ✓
                                                    </button>
                                                    <button 
                                                        className="btn btn-outline-info" 
                                                        onClick={() => updateUserStatus(rfq.job_id, 'completed')}
                                                        title="Mark as Completed"
                                                    >
                                                        ✔✔
                                                    </button>
                                                    <button 
                                                        className="btn btn-outline-danger" 
                                                        onClick={() => updateUserStatus(rfq.job_id, 'ignore')}
                                                        title="Ignore this RFQ"
                                                    >
                                                        ✗
                                                    </button>
                                                </div>
                                            </td>
                        </tr>
                                    ))
                                )}
                </tbody>
            </table>
                    </div>
                </div>
            </div>

            {/* Admin Section - Collapsed by default */}
            <div className="card mt-4">
                <div className="card-body">
                    <details>
                        <summary className="fw-bold" style={{cursor: 'pointer'}}>
                            Advanced Options
                        </summary>
                        <div className="mt-3">
                            <h5>Add City</h5>
                            <div className="row g-2 mb-3">
                                <div className="col-md-4">
                                    <input 
                                        type="text" 
                                        className="form-control" 
                                        placeholder="Organization" 
                                        onChange={e => setNewCity({...newCity, organization: e.target.value})} 
                                    />
                                </div>
                                <div className="col-md-6">
                                    <input 
                                        type="text" 
                                        className="form-control" 
                                        placeholder="URL" 
                                        onChange={e => setNewCity({...newCity, url: e.target.value})} 
                                    />
                                </div>
                                <div className="col-md-2">
                                    <button className="btn btn-primary w-100" onClick={addCity}>Add City</button>
                                </div>
                            </div>

                            <hr />

                            <h5>Manual Input</h5>
                            <div className="mb-3">
                                <input 
                                    type="text" 
                                    className="form-control mb-2" 
                                    placeholder="Organization Name (e.g., City of Chandler)" 
                                    value={screenshotOrg}
                                    onChange={e => setScreenshotOrg(e.target.value)} 
                                />
                                <input 
                                    type="url" 
                                    className="form-control mb-2" 
                                    placeholder="Job URL (e.g., https://procurement.az.gov/...)" 
                                    value={pasteUrl}
                                    onChange={e => setPasteUrl(e.target.value)} 
                                />
                                <textarea 
                                    className="form-control mb-2" 
                                    placeholder="Paste RFQ text here (Project number, title, due date, description...)" 
                                    value={pasteText} 
                                    onChange={e => setPasteText(e.target.value)} 
                                    rows="4"
                                />
                                <button className="btn btn-secondary" onClick={parseText}>Parse Text</button>
                            </div>

                            <hr />

                            <h5>Upload Screenshot</h5>
                            <div className="mb-3">
                                <input 
                                    type="file" 
                                    className="form-control mb-2" 
                                    accept="image/*" 
                                    onChange={e => setScreenshot(e.target.files[0])} 
                                />
                                <button 
                                    className="btn btn-secondary" 
                                    onClick={uploadScreenshot} 
                                    disabled={!screenshot}
                                >
                                    Upload Screenshot
                                </button>
                            </div>
                        </div>
                    </details>
                </div>
            </div>
        </div>
    );
}

export default App;