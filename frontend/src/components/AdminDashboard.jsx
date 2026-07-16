import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getLeads, getStats, updateLeadStatus, deleteLead, exportCSV, exportExcel, getImageUrl } from '../api';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    requirement_type: '',
    customer_type: '',
    search: '',
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const navigate = useNavigate();

  const statusOptions = ['all', 'new', 'contacted', 'converted', 'closed'];
  const requirementOptions = ['all', 'PLC', 'HMI', 'SCADA', 'Servo', 'IoT', 'Full_Requirement', 'ID Card Capture'];
  const customerOptions = ['all', 'End_Customer', 'Distributor', 'Manufacturer', 'Other'];

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [leadsData, statsData] = await Promise.all([
        getLeads(filters),
        getStats(),
      ]);
      setLeads(leadsData.leads || []);
      setStats(statsData);
    } catch (error) {
      toast.error('Failed to fetch data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const email = localStorage.getItem('user_email') || 'Admin';
    setUserEmail(email);
    fetchData();
  }, [fetchData]);

  const handleStatusUpdate = async (id, newStatus) => {
    try {
      await updateLeadStatus(id, newStatus);
      toast.success(`Lead ${id} status updated to ${newStatus}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm(`Are you sure you want to delete lead ${id}?`)) {
      try {
        await deleteLead(id);
        toast.success(`Lead ${id} deleted`);
        fetchData();
      } catch (error) {
        toast.error('Failed to delete lead');
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const handleImageClick = (imageUrl, name, company) => {
    if (imageUrl) {
      setSelectedImage({
        url: getImageUrl(imageUrl),
        name: name,
        company: company,
      });
    }
  };

  const closeImageModal = () => {
    setSelectedImage(null);
  };

  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = '/logo.png';
    e.target.alt = 'Image not available';
  };

  const getStatusColor = (status) => {
    const colors = {
      new: '#FFB74D',
      contacted: '#64B5F6',
      converted: '#81C784',
      closed: '#E0E0E0',
    };
    return colors[status] || '#E0E0E0';
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="spinner"></div>
        <p>Loading leads...</p>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div className="header-left">
          <h1>📊 Lead Management Dashboard</h1>
          <span className="user-info">Welcome, {userEmail}</span>
        </div>
        <div className="admin-actions">
          <button onClick={exportCSV} className="export-btn csv">📄 Export CSV</button>
          <button onClick={exportExcel} className="export-btn excel">📊 Export Excel</button>
          <button onClick={handleLogout} className="logout-btn">🚪 Logout</button>
        </div>
      </header>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{stats.total_leads}</span>
            <span className="stat-label">Total Leads</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.new_count}</span>
            <span className="stat-label">New</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.contacted_count}</span>
            <span className="stat-label">Contacted</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.converted_count}</span>
            <span className="stat-label">Converted</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.today_leads}</span>
            <span className="stat-label">Today's Leads</span>
          </div>
          <div className="stat-card highlight">
            <span className="stat-value">{stats.with_images || 0}</span>
            <span className="stat-label">📸 With ID Cards</span>
          </div>
        </div>
      )}

      <div className="filters-container">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="filter-select"
        >
          {statusOptions.map(status => (
            <option key={status} value={status === 'all' ? '' : status}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </option>
          ))}
        </select>

        <select
          value={filters.requirement_type}
          onChange={(e) => setFilters({ ...filters, requirement_type: e.target.value })}
          className="filter-select"
        >
          {requirementOptions.map(req => (
            <option key={req} value={req === 'all' ? '' : req}>
              {req === 'all' ? 'All Requirements' : req}
            </option>
          ))}
        </select>

        <select
          value={filters.customer_type}
          onChange={(e) => setFilters({ ...filters, customer_type: e.target.value })}
          className="filter-select"
        >
          {customerOptions.map(cust => (
            <option key={cust} value={cust === 'all' ? '' : cust}>
              {cust === 'all' ? 'All Customers' : cust}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search by name, email, company..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="search-input"
        />
      </div>

      <div className="table-container">
        {leads.length === 0 ? (
          <div className="no-data">
            <p>No leads found</p>
          </div>
        ) : (
          <table className="leads-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Image</th>
                <th>Name</th>
                <th>Company</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Requirement</th>
                <th>Customer Type</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leads.map(lead => (
                <tr key={lead.id}>
                  <td>#{lead.id}</td>
                  <td>
                    {lead.image_url ? (
                      <img
                        src={getImageUrl(lead.image_url)}
                        alt="ID Card"
                        className="id-thumbnail"
                        onClick={() => handleImageClick(lead.image_url, lead.name, lead.company)}
                        onError={handleImageError}
                        title="Click to view full size"
                      />
                    ) : (
                      <span className="no-image">—</span>
                    )}
                  </td>
                  <td>{lead.name}</td>
                  <td>{lead.company}</td>
                  <td>{lead.email}</td>
                  <td>{lead.phone || '-'}</td>
                  <td>
                    <span className="requirement-badge">{lead.requirement_type}</span>
                  </td>
                  <td>{lead.customer_type}</td>
                  <td>
                    <select
                      value={lead.status}
                      onChange={(e) => handleStatusUpdate(lead.id, e.target.value)}
                      style={{ backgroundColor: getStatusColor(lead.status) }}
                      className="status-select"
                    >
                      <option value="new">New</option>
                      <option value="contacted">Contacted</option>
                      <option value="converted">Converted</option>
                      <option value="closed">Closed</option>
                    </select>
                  </td>
                  <td>{new Date(lead.created_at).toLocaleDateString()}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(lead.id)}
                      className="delete-btn"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedImage && (
        <div className="image-modal" onClick={closeImageModal}>
          <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="image-modal-close" onClick={closeImageModal}>✕</button>
            <img
              src={selectedImage.url}
              alt="ID Card"
              className="image-modal-img"
              onError={handleImageError}
            />
            <div className="image-modal-info">
              <h4>{selectedImage.name}</h4>
              <p>{selectedImage.company}</p>
              <span className="image-tag">📸 ID Card</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;