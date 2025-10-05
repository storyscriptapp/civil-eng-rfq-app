import React, { useState, useEffect } from 'react';
import './App.css';

function JobDetails({ jobId, auth, onBack }) {
    const [job, setJob] = useState(null);
    const [scrapeHistory, setScrapeHistory] = useState([]);
    const [journalEntries, setJournalEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingTitle, setEditingTitle] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [newJournalEntry, setNewJournalEntry] = useState('');
    const [userName, setUserName] = useState(localStorage.getItem('rfq_user_name') || 'User');

    useEffect(() => {
        loadJobDetails();
    }, [jobId]);

    const loadJobDetails = () => {
        fetch(`http://localhost:8000/job_details/${jobId}`)
            .then(res => res.json())
            .then(data => {
                setJob(data.job);
                setNewTitle(data.job.title);
                setScrapeHistory(data.scrape_history);
                setJournalEntries(data.journal_entries);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error loading job details:', err);
                setLoading(false);
            });
    };

    const updateTitle = () => {
        fetch('http://localhost:8000/update_job_details', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Basic ${auth}`
            },
            body: JSON.stringify({ job_id: jobId, title: newTitle })
        })
            .then(res => res.json())
            .then(data => {
                setJob({ ...job, title: newTitle });
                setEditingTitle(false);
                console.log('Title updated:', data);
            })
            .catch(err => console.error('Error updating title:', err));
    };

    const addJournalEntry = () => {
        if (!newJournalEntry.trim()) return;

        // Save user name to localStorage
        localStorage.setItem('rfq_user_name', userName);

        fetch('http://localhost:8000/add_journal_entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_id: jobId,
                entry_text: newJournalEntry,
                user_name: userName
            })
        })
            .then(res => res.json())
            .then(data => {
                setJournalEntries([data.entry, ...journalEntries]);
                setNewJournalEntry('');
                console.log('Journal entry added:', data);
            })
            .catch(err => console.error('Error adding journal entry:', err));
    };

    if (loading) {
        return <div className="container mt-5"><p>Loading job details...</p></div>;
    }

    if (!job) {
        return <div className="container mt-5"><p>Job not found.</p></div>;
    }

    return (
        <div className="container mt-4">
            {/* Back button */}
            <button className="btn btn-secondary mb-3" onClick={onBack}>
                ← Back to RFQs List
            </button>

            {/* Job Header */}
            <div className="card mb-3">
                <div className="card-body">
                    <div className="row">
                        <div className="col-md-8">
                            <h5 className="card-title">
                                {editingTitle ? (
                                    <div className="input-group">
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={newTitle}
                                            onChange={(e) => setNewTitle(e.target.value)}
                                        />
                                        <button className="btn btn-success" onClick={updateTitle}>
                                            Save
                                        </button>
                                        <button className="btn btn-secondary" onClick={() => {
                                            setEditingTitle(false);
                                            setNewTitle(job.title);
                                        }}>
                                            Cancel
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        {job.title}
                                        <button
                                            className="btn btn-sm btn-outline-secondary ms-2"
                                            onClick={() => setEditingTitle(true)}
                                        >
                                            ✏️ Edit
                                        </button>
                                    </>
                                )}
                            </h5>
                            <p className="text-muted mb-1">
                                <strong>Organization:</strong> {job.organization}
                            </p>
                            <p className="text-muted mb-1">
                                <strong>Job ID:</strong> <span className="font-monospace">{job.job_id}</span>
                            </p>
                            <p className="text-muted mb-1">
                                <strong>Org RFP #:</strong> {job.rfp_number}
                            </p>
                        </div>
                        <div className="col-md-4 text-end">
                            <p><strong>Status:</strong> 
                                {job.user_status === 'new' && <span className="badge bg-success ms-2">NEW</span>}
                                {job.user_status === 'pursuing' && <span className="badge bg-warning ms-2">Pursuing</span>}
                                {job.user_status === 'completed' && <span className="badge bg-info ms-2">Completed</span>}
                                {job.user_status === 'declined' && <span className="badge bg-secondary ms-2">Declined</span>}
                                {job.user_status === 'ignore' && <span className="badge bg-danger ms-2">Ignored</span>}
                            </p>
                            <p><strong>Work Type:</strong> <span className="badge bg-light text-dark">{job.work_type}</span></p>
                            <p><strong>Due Date:</strong> {job.due_date}</p>
                            <p>
                                <a href={job.link} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
                                    View RFQ →
                                </a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Scrape History */}
            <div className="card mb-3">
                <div className="card-header">
                    <h6 className="mb-0">Scrape History</h6>
                </div>
                <div className="card-body">
                    <p className="text-muted mb-2">
                        <strong>First Seen:</strong> {new Date(job.first_seen).toLocaleString()}
                    </p>
                    <p className="text-muted mb-2">
                        <strong>Last Seen:</strong> {new Date(job.last_seen).toLocaleString()}
                    </p>
                    <p className="text-muted mb-2">
                        <strong>Added By:</strong> 
                        <span className={`badge ms-2 ${job.added_by === 'parsed' ? 'bg-info' : 'bg-success'}`}>
                            {job.added_by === 'parsed' ? '📝 Manual Parsing' : '🤖 Scraper'}
                        </span>
                    </p>
                    {scrapeHistory.length > 0 && (
                        <div className="mt-3">
                            <small className="text-muted">This job has been scraped {scrapeHistory.length} time(s)</small>
                        </div>
                    )}
                </div>
            </div>

            {/* Job Info - Extra details from parsing */}
            {job.job_info && (
                <div className="card mb-3">
                    <div className="card-header">
                        <h6 className="mb-0">Additional Job Information</h6>
                    </div>
                    <div className="card-body">
                        <pre className="mb-0" style={{whiteSpace: 'pre-wrap', fontSize: '0.9rem'}}>
                            {job.job_info}
                        </pre>
                    </div>
                </div>
            )}

            {/* Journal Entries */}
            <div className="card">
                <div className="card-header">
                    <h6 className="mb-0">Project Journal</h6>
                </div>
                <div className="card-body">
                    {/* Add new entry */}
                    <div className="mb-4">
                        <label className="form-label"><strong>Add Journal Entry</strong></label>
                        <div className="row mb-2">
                            <div className="col-md-3">
                                <input
                                    type="text"
                                    className="form-control"
                                    placeholder="Your name"
                                    value={userName}
                                    onChange={(e) => setUserName(e.target.value)}
                                />
                            </div>
                        </div>
                        <textarea
                            className="form-control mb-2"
                            rows="3"
                            placeholder="e.g., 'Submitted to BethAnn for proposal generation' or 'Called XYZ Construction for partnering opportunity'"
                            value={newJournalEntry}
                            onChange={(e) => setNewJournalEntry(e.target.value)}
                        ></textarea>
                        <button
                            className="btn btn-primary"
                            onClick={addJournalEntry}
                            disabled={!newJournalEntry.trim()}
                        >
                            Add Entry
                        </button>
                    </div>

                    {/* Display entries */}
                    {journalEntries.length === 0 ? (
                        <p className="text-muted">No journal entries yet. Start tracking your progress!</p>
                    ) : (
                        <div>
                            {journalEntries.map((entry, index) => (
                                <div key={index}>
                                    <div className="p-3 bg-light rounded mb-2">
                                        <div className="d-flex justify-content-between mb-2">
                                            <strong>{entry.user_name}</strong>
                                            <small className="text-muted">
                                                {new Date(entry.created_at).toLocaleString()}
                                            </small>
                                        </div>
                                        <p className="mb-0">{entry.text}</p>
                                    </div>
                                    {index < journalEntries.length - 1 && <hr style={{margin: '0.5rem 0'}} />}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default JobDetails;

