import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { submitLead } from '../api';
import './LeadForm.css';

const LeadForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    requirement_types: [],
    customer_type: '',
    other_customer_type: '',
    message: '',
    image: null,
  });

  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const savedImage = sessionStorage.getItem('captured_image');
    if (savedImage) {
      setFormData(prev => ({ ...prev, image: savedImage }));
      toast.success('📸 ID Card image loaded from capture!');
    }
  }, []);

  const requirementOptions = [
    { value: 'PLC', label: '🔷 PLC Query' },
    { value: 'HMI', label: '📺 HMI Requirement' },
    { value: 'SCADA', label: '📊 SCADA' },
    { value: 'Servo', label: '⚙️ Servo & Motors' },
    { value: 'IoT', label: '☁️ IoT' },
    { value: 'Full_Requirement', label: '📋 Full Requirement' },
  ];

  const customerOptions = [
    { value: 'End_Customer', label: '👤 End Customer' },
    { value: 'Distributor', label: '🏢 Distributor' },
    { value: 'Manufacturer', label: '🏭 Manufacturer' },
    { value: 'Other', label: '📌 Other' },
  ];

  const toggleRequirement = (value) => {
    setFormData(prev => {
      const current = prev.requirement_types || [];
      if (current.includes(value)) {
        return { ...prev, requirement_types: current.filter(v => v !== value) };
      } else {
        return { ...prev, requirement_types: [...current, value] };
      }
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Please enter your name');
      return;
    }
    if (!formData.company.trim()) {
      toast.error('Please enter your company name');
      return;
    }
    if (!formData.email.trim()) {
      toast.error('Please enter your email');
      return;
    }
    if (formData.requirement_types.length === 0) {
      toast.error('Please select at least one requirement');
      return;
    }
    if (!formData.customer_type) {
      toast.error('Please select your customer type');
      return;
    }
    if (formData.customer_type === 'Other' && !formData.other_customer_type.trim()) {
      toast.error('Please specify your customer type');
      return;
    }
    if (formData.phone && !/^\d{10}$/.test(formData.phone)) {
    toast.error('Phone number must be exactly 10 digits');
    return;
    }

    setLoading(true);
    try {
      const submitData = {
        name: formData.name,
        company: formData.company,
        email: formData.email,
        phone: formData.phone || '',
        requirement_type: formData.requirement_types.join(', '),
        customer_type: formData.customer_type,
        other_customer_type: formData.other_customer_type || '',
        message: formData.message || '',
        source: 'web_form',
        image_url: formData.image || null,
      };
      
      await submitLead(submitData);
      sessionStorage.removeItem('captured_image');
      setSubmitted(true);
      toast.success('✅ Lead submitted successfully!');
    } catch (error) {
      toast.error('❌ Failed to submit. Please try again.');
      console.error('Submission error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: '',
      company: '',
      email: '',
      phone: '',
      requirement_types: [],
      customer_type: '',
      other_customer_type: '',
      message: '',
      image: null,
    });
    sessionStorage.removeItem('captured_image');
    setSubmitted(false);
  };

  const removeImage = () => {
    setFormData(prev => ({ ...prev, image: null }));
    sessionStorage.removeItem('captured_image');
    toast.success('Image removed');
  };

  const handleDirectSave = async () => {
    const imageData = sessionStorage.getItem('captured_image');
    if (!imageData) {
      toast.error('No image captured! Please capture an ID card first.');
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        name: 'Visitor - ' + new Date().toLocaleString(),
        company: 'Walk-in Visitor',
        email: '',
        phone: '',
        requirement_type: 'ID Card Capture',
        customer_type: 'Other',
        other_customer_type: 'Walk-in Visitor',
        message: 'ID Card captured via camera on ' + new Date().toLocaleString(),
        source: 'camera_capture',
        image_url: imageData,
      };
      
      await submitLead(submitData);
      sessionStorage.removeItem('captured_image');
      toast.success('✅ ID Card saved successfully!');
      setFormData(prev => ({ ...prev, image: null }));
    } catch (error) {
      toast.error('❌ Failed to save. Please try again.');
      console.error('Save error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="success-container">
        <div className="success-icon">🎉</div>
        <h2>Thank You!</h2>
        <p>Your enquiry has been submitted successfully.</p>
        <p>Our team will contact you within 24 hours.</p>
        <button onClick={handleReset} className="submit-btn">
          Submit Another Enquiry
        </button>
      </div>
    );
  }

  return (
    <div className="form-container">
      <div className="form-header">
        <h1>FATEK Leads Form</h1>
        <p>Tell us about your requirements and we'll get back to you</p>
      </div>

      <form onSubmit={handleSubmit} className="lead-form">
        {formData.image && (
          <div className="form-group">
            <label>📸 Captured ID Card</label>
            <div className="image-preview-container">
              <img 
                src={formData.image} 
                alt="ID Card" 
                className="image-preview"
              />
              <button 
                type="button" 
                className="remove-image-btn"
                onClick={removeImage}
              >
                ✕ Remove
              </button>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button 
                type="button" 
                className="direct-save-btn"
                onClick={handleDirectSave}
                disabled={loading}
              >
                💾 Save ID Card Only
              </button>
              <span style={{ fontSize: '12px', color: '#666', alignSelf: 'center' }}>
                (Skip form, save directly)
              </span>
            </div>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="name">Full Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter your full name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="company">Organization Name *</label>
          <input
            type="text"
            id="company"
            name="company"
            value={formData.company}
            onChange={handleChange}
            placeholder="Enter your organization name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email Address *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email address"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <input
            type="tel"
            id="phone"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            maxLength="10"
            pattern="[0-9]{10}"
            placeholder="Enter your phone number (optional)"
          />
        </div>

        <div className="form-group">
          <label>Type of Requirement * <span style={{ fontSize: '12px', color: '#666', fontWeight: 'normal' }}>(Select multiple)</span></label>
          <div className="button-group multiple-select">
            {requirementOptions.map(option => {
              const isSelected = formData.requirement_types.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  className={`option-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => toggleRequirement(option.value)}
                >
                  {option.label}
                  {isSelected && <span className="checkmark"> ✓</span>}
                </button>
              );
            })}
          </div>
          {formData.requirement_types.length > 0 && (
            <div className="selected-count">
              Selected: {formData.requirement_types.length} requirement(s)
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Type of Customer *</label>
          <div className="button-group">
            {customerOptions.map(option => (
              <button
                key={option.value}
                type="button"
                className={`option-btn ${formData.customer_type === option.value ? 'active' : ''}`}
                onClick={() => setFormData(prev => ({ ...prev, customer_type: option.value }))}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {formData.customer_type === 'Other' && (
          <div className="form-group">
            <label htmlFor="other_customer_type">Please specify your customer type *</label>
            <input
              type="text"
              id="other_customer_type"
              name="other_customer_type"
              value={formData.other_customer_type}
              onChange={handleChange}
              placeholder="Enter your customer type"
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="message">Additional Details</label>
          <textarea
            id="message"
            name="message"
            value={formData.message}
            onChange={handleChange}
            placeholder="Tell us more about your requirements (optional)"
            rows="4"
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Enquiry'}
        </button>
      </form>
    </div>
  );
};

export default LeadForm;