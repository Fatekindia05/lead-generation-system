import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import LeadForm from './components/LeadForm';
import AdminDashboard from './components/AdminDashboard';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import CameraCapture from './components/CameraCapture';
import './App.css';

const Navigation = () => {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showCamera, setShowCamera] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    setIsAuthenticated(!!token);
  }, [location]);

  const isLoginPage = location.pathname === '/login';

  const handleCaptureComplete = () => {
    setShowCamera(false);
  };

  const handleCancelCapture = () => {
    setShowCamera(false);
  };

  return (
    <>
      <nav className="nav-bar">
        <div className="nav-brand">
          <img 
            src="/logo.png" 
            alt="Company Logo" 
            className="company-logo"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '/logo192.png';
            }}
          />
          <span className="brand-text" style={{ fontWeight: 'bold', fontSize: '2.0rem', fontFamily: 'Arial, sans-serif'}}>FATEK</span>
        </div>
        <div className="nav-links">
          <Link to="/" className="nav-link">📝 Form</Link>
          
          <button 
            className="nav-link capture-btn" 
            onClick={() => setShowCamera(true)}
            title="Capture ID Card"
          >
            📸 Capture
          </button>
          
          {isAuthenticated ? (
            <Link to="/admin" className="nav-link">📊 Dashboard</Link>
          ) : (
            !isLoginPage && <Link to="/login" className="nav-link">🔐 Login</Link>
          )}
        </div>
      </nav>

      {showCamera && (
        <CameraCapture
          onCapture={handleCaptureComplete}
          onCancel={handleCancelCapture}
        />
      )}
    </>
  );
};

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        
        <Routes>
          <Route path="/" element={<LeadForm />} />
          <Route path="/login" element={<Login />} />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
        </Routes>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;