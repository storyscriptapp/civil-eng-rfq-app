// API Configuration
// In development (npm start), use localhost:8000
// In production (built and served from FastAPI), use relative URLs

const isProduction = process.env.NODE_ENV === 'production';

export const API_BASE_URL = isProduction 
  ? window.location.origin  // Use same origin as the app
  : 'http://localhost:8000'; // Development server

export default API_BASE_URL;

