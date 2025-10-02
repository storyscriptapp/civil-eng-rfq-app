import React, { useEffect, useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
    const [rfqs, setRfqs] = useState([]);
    const [cities, setCities] = useState([]);
    const [newCity, setNewCity] = useState({ organization: '', url: '', row_selector: '', cell_count: 4, is_dynamic: false, manual: false });
    const [pasteText, setPasteText] = useState('');
    const [screenshot, setScreenshot] = useState(null);
    const [screenshotOrg, setScreenshotOrg] = useState('');

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
        fetch('http://localhost:8000/run_scraper', { method: 'POST' })
            .then(res => res.json())
            .then(data => console.log('Scraper:', data))
            .catch(err => console.error('Error running scraper:', err));
    };

    const parseText = () => {
        fetch('http://localhost:8000/parse_text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: pasteText, organization: screenshotOrg })
        })
            .then(res => res.json())
            .then(data => {
                setRfqs([...rfqs, ...data.rfqs]);
                console.log('Parsed RFQs:', data);
            })
            .catch(err => console.error('Error parsing text:', err));
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

    return (
        <div className="container">
            <h1>RFQ App</h1>
            <h2>RFQs</h2>
            <table className="table">
                <thead>
                    <tr>
                        <th>Organization</th>
                        <th>Title</th>
                        <th>Work Type</th>
                        <th>Due Date</th>
                        <th>Completed</th>
                        <th>Hide</th>
                    </tr>
                </thead>
                <tbody>
                    {rfqs.map((rfq, index) => (
                        <tr key={index}>
                            <td>{rfq.organization}</td>
                            <td><a href={rfq.link || '#'} target="_blank" rel="noopener noreferrer">{rfq.title}</a></td>
                            <td>{rfq.work_type}</td>
                            <td>{rfq.due_date}</td>
                            <td><input type="checkbox" checked={rfq.completed} onChange={() => {}} /></td>
                            <td><input type="checkbox" checked={rfq.hide} onChange={() => {}} /></td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <h2>Add City</h2>
            <input type="text" placeholder="Organization" onChange={e => setNewCity({...newCity, organization: e.target.value})} />
            <input type="text" placeholder="URL" onChange={e => setNewCity({...newCity, url: e.target.value})} />
            <button onClick={addCity}>Add City</button>
            <button onClick={runScraper}>Run Scraper</button>
            <h2>Manual Input</h2>
            <input type="text" placeholder="Organization for Manual Input" onChange={e => setScreenshotOrg(e.target.value)} />
            <textarea placeholder="Paste RFQ text here" value={pasteText} onChange={e => setPasteText(e.target.value)} style={{ width: '100%', height: '100px' }} />
            <button onClick={parseText}>Parse Text</button>
            <h2>Upload Screenshot</h2>
            <input type="file" accept="image/*" onChange={e => setScreenshot(e.target.files[0])} />
            <button onClick={uploadScreenshot} disabled={!screenshot}>Upload Screenshot</button>
        </div>
    );
}

export default App;