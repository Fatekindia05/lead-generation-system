import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      if (email === 'admin@fatek.com' && password === 'fatek2026') {
        localStorage.setItem('auth_token', 'demo_token');
        localStorage.setItem('user_email', email);
        toast.success('Login successful!');
        navigate('/admin');
      } else {
        toast.error('Invalid credentials. Use admin@fatek.com / fatek2026');
      }
    } catch (error) {
      toast.error('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <img src="/logo192.png" alt="Logo" className="login-logo-img" />
          </div>
          <h2>Admin Login</h2>
          <p>Enter your credentials to access the dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@fatek.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Logging in...' : 'Sign In'}
          </button>

          <div className="login-footer">
            <p>Demo credentials:</p>
            <code>admin@fatek.com / fatek2026</code>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;