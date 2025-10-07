import React, { useState, useEffect } from 'react';
import './CitiesList.css';
import API_BASE_URL from './config';

function CitiesList({ auth, onCitySelect, onBack }) {
  const [cities, setCities] = useState([]);
  const [selectedCities, setSelectedCities] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/cities`);
      const data = await response.json();
      setCities(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching cities:', error);
      setLoading(false);
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedCities = [...cities].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const toggleCitySelection = (cityName) => {
    const newSelected = new Set(selectedCities);
    if (newSelected.has(cityName)) {
      newSelected.delete(cityName);
    } else {
      newSelected.add(cityName);
    }
    setSelectedCities(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedCities.size === cities.length) {
      setSelectedCities(new Set());
    } else {
      setSelectedCities(new Set(cities.map(c => c.name)));
    }
  };

  const handleScrapeSelected = async () => {
    if (selectedCities.size === 0) {
      alert('Please select at least one city to scrape');
      return;
    }

    const citiesList = [...selectedCities];
    const confirmed = window.confirm(
      `Start scraping ${citiesList.length} cities?\n\n${citiesList.join('\n')}\n\nA new terminal window will open showing progress.`
    );

    if (!confirmed) return;

    try {
      const response = await fetch(`${API_BASE_URL}/run_scraper`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth}`
        },
        body: JSON.stringify({ cities: citiesList })
      });

      const data = await response.json();
      alert(`✅ Scraper started for ${citiesList.length} cities!\n\nCheck the terminal window for progress.`);
    } catch (error) {
      console.error('Error starting scraper:', error);
      alert('❌ Error starting scraper. Make sure the API server is running.');
    }
  };

  if (loading) {
    return <div className="loading">Loading cities...</div>;
  }

  return (
    <div className="cities-container">
      <div className="cities-header">
        <button onClick={onBack} className="back-button">← Back to RFQs</button>
        <h1>Cities & Organizations</h1>
        <div className="cities-actions">
          <button 
            onClick={handleScrapeSelected} 
            className="scrape-button"
            disabled={selectedCities.size === 0}
          >
            Scrape Selected ({selectedCities.size})
          </button>
        </div>
      </div>

      <div className="cities-table-container">
        <table className="cities-table">
          <thead>
            <tr>
              <th>
                <input 
                  type="checkbox" 
                  checked={selectedCities.size === cities.length && cities.length > 0}
                  onChange={toggleSelectAll}
                />
              </th>
              <th onClick={() => handleSort('name')} className="sortable">
                City/Organization {sortConfig.key === 'name' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('population_current')} className="sortable">
                Population (2025) {sortConfig.key === 'population_current' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('population_2020')} className="sortable">
                Population (2020) {sortConfig.key === 'population_2020' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th>Contact Name</th>
              <th onClick={() => handleSort('avg_household_income')} className="sortable">
                Avg. Household Income {sortConfig.key === 'avg_household_income' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th>Bonds (Upcoming)</th>
              <th>Bonds (Last Election)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedCities.map((city) => (
              <tr key={city.name}>
                <td>
                  <input 
                    type="checkbox" 
                    checked={selectedCities.has(city.name)}
                    onChange={() => toggleCitySelection(city.name)}
                  />
                </td>
                <td>
                  <button 
                    onClick={() => onCitySelect(city.name)} 
                    className="city-name-link"
                  >
                    {city.name}
                  </button>
                </td>
                <td className="data-placeholder">
                  {city.population_current || '—'}
                </td>
                <td className="data-placeholder">
                  {city.population_2020 || '—'}
                </td>
                <td className="data-placeholder">
                  {city.contact_name || '—'}
                </td>
                <td className="data-placeholder">
                  {city.avg_household_income ? `$${city.avg_household_income.toLocaleString()}` : '—'}
                </td>
                <td className="data-placeholder">
                  {city.bonds_upcoming !== null ? (city.bonds_upcoming ? 'Yes' : 'No') : '—'}
                </td>
                <td className="data-placeholder">
                  {city.bonds_last !== null ? (city.bonds_last ? 'Yes' : 'No') : '—'}
                </td>
                <td>
                  <span className={`status-badge ${city.is_active ? 'active' : 'inactive'}`}>
                    {city.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cities-footer">
        <p>Total: {cities.length} cities/organizations</p>
        <p className="placeholder-note">
          ℹ️ Data fields marked with "—" are placeholders. Click city names to view/edit profiles.
        </p>
      </div>
    </div>
  );
}

export default CitiesList;

