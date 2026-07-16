import React, { useState, useRef, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { submitLead } from '../api';
import './CameraCapture.css';

const CameraCapture = ({ onCapture, onCancel }) => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    const isMobileDevice = /Android|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(
      navigator.userAgent
    );
    setIsMobile(isMobileDevice);
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraReady(false);
  }, []);

  const startCamera = useCallback(async () => {
    if (streamRef.current) {
      stopCamera();
    }

    setIsLoading(true);
    setError(null);
    setCameraReady(false);

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API not supported in this browser');
      }

      const constraintsList = [
        { video: { width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
        { video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
        { video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
        { video: true, audio: false },
      ];

      let stream = null;
      let lastError = null;

      for (const constraints of constraintsList) {
        try {
          stream = await navigator.mediaDevices.getUserMedia(constraints);
          break;
        } catch (err) {
          lastError = err;
          continue;
        }
      }

      if (!stream) {
        throw lastError || new Error('Could not access camera with any configuration');
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        videoRef.current.onloadedmetadata = () => {
          videoRef.current
            .play()
            .then(() => {
              setCameraReady(true);
              setIsLoading(false);
            })
            .catch(err => {
              console.error('❌ Play failed:', err);
              setError('Failed to start video playback. Please try again.');
              setIsLoading(false);
            });
        };

        videoRef.current.onerror = () => {
          setError('Video stream error occurred');
          setIsLoading(false);
        };
      } else {
        setError('Camera preview failed to initialize. Please retry.');
        setIsLoading(false);
      }
    } catch (err) {
      console.error('❌ Final camera error:', err);
      let errorMessage = 'Unable to access camera. Please check permissions.';

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera permission denied. Please allow camera access in your browser settings.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = 'No camera found on this device. Please connect a camera.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = 'Camera is in use by another application. Please close other apps.';
      } else if (err.message && err.message.includes('getUserMedia')) {
        errorMessage = "Your browser doesn't support camera access. Please use Chrome or Safari.";
      }

      setError(errorMessage);
      setIsLoading(false);
      toast.error(errorMessage);
    }
  }, [stopCamera]);

  useEffect(() => {
    const timer = setTimeout(() => {
      startCamera();
    }, 500);

    return () => {
      clearTimeout(timer);
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) {
      toast.error('Camera not ready');
      return;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = canvas.toDataURL('image/jpeg', 0.9);
      setCapturedImage(imageData);
      stopCamera();
      toast.success('📸 Image captured! Click Confirm to save.');
    } catch (err) {
      console.error('Capture error:', err);
      toast.error('Failed to capture image');
    }
  };

  const confirmAndSave = async () => {
    if (!capturedImage) {
      toast.error('No image to save!');
      return;
    }

    setIsSaving(true);
    try {
      const leadData = {
        name: 'Visitor - ' + new Date().toLocaleString(),
        company: 'Walk-in Visitor',
        email: '',
        phone: '',
        requirement_type: 'ID Card Capture',
        customer_type: 'Other',
        other_customer_type: 'Walk-in Visitor',
        message: 'ID Card captured via camera on ' + new Date().toLocaleString(),
        source: 'camera_capture',
        image_url: capturedImage,
      };

      console.log('Saving image with empty email...', leadData);
      
      const response = await submitLead(leadData);
      console.log('Save response:', response);
      
      setCapturedImage(null);
      toast.success('✅ ID Card saved successfully to database!');
      
      setTimeout(() => {
        onCancel();
      }, 1500);
      
    } catch (error) {
      console.error('Save error:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        toast.error(`❌ Failed to save: ${error.response.data?.detail || 'Validation error'}`);
      } else {
        toast.error('❌ Failed to save. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const retakeImage = () => {
    setCapturedImage(null);
    startCamera();
  };

  const closeCamera = () => {
    stopCamera();
    setCapturedImage(null);
    onCancel();
  };

  const switchCamera = async () => {
    if (!streamRef.current) {
      toast.error('No camera stream to switch');
      return;
    }

    try {
      const tracks = streamRef.current.getVideoTracks();
      if (tracks.length === 0) {
        toast.error('No video track found');
        return;
      }

      const settings = tracks[0].getSettings();
      const currentFacing = settings.facingMode || 'environment';
      const newFacing = currentFacing === 'environment' ? 'user' : 'environment';

      stopCamera();

      const constraints = {
        video: { facingMode: newFacing, width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current
            .play()
            .then(() => {
              setCameraReady(true);
              toast.success(`Switched to ${newFacing === 'user' ? 'front' : 'back'} camera`);
            })
            .catch(err => {
              console.error('Switch play failed:', err);
              toast.error('Failed to switch camera');
            });
        };
      }
    } catch (err) {
      console.error('Switch camera error:', err);
      toast.error('Failed to switch camera');
      startCamera();
    }
  };

  const handleRetry = () => {
    setError(null);
    setIsLoading(true);
    startCamera();
  };

  const showPreviewContainer = !error && !capturedImage;

  return (
    <div className="camera-overlay">
      <div className="camera-modal">
        <div className="camera-header">
          <h3>📸 Capture ID Card</h3>
          <button className="close-btn" onClick={closeCamera}>✕</button>
        </div>

        <div className="camera-body">
          {error && (
            <div className="camera-error">
              <div className="error-icon">⚠️</div>
              <h4>Camera Error</h4>
              <p>{error}</p>
              <div className="error-actions">
                <button className="retry-btn" onClick={handleRetry}>🔄 Retry</button>
                <button className="skip-btn" onClick={closeCamera}>Skip Camera</button>
              </div>
              <div className="error-tips">
                <p>💡 Troubleshooting Tips:</p>
                <ul>
                  <li>Click the camera icon in your browser address bar and allow access</li>
                  <li>For Chrome: Settings → Privacy → Camera → Allow</li>
                  <li>For Safari: Settings → Privacy → Camera → Allow</li>
                  <li>Close other apps that might be using the camera</li>
                  <li>Try refreshing the page</li>
                </ul>
              </div>
            </div>
          )}

          {showPreviewContainer && !capturedImage && (
            <div className="camera-preview-container">
              <div className="camera-preview">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="video-preview"
                  style={{ display: cameraReady ? 'block' : 'none' }}
                />

                {isLoading && (
                  <div className="camera-loading">
                    <div className="spinner"></div>
                    <p>Starting camera...</p>
                    <p className="loading-hint">Please grant camera permission when prompted</p>
                  </div>
                )}

                {!isLoading && !cameraReady && (
                  <div className="camera-placeholder">
                    <div className="camera-icon">📷</div>
                    <p>Camera not ready. Click start to initialize.</p>
                    <button className="start-camera-btn" onClick={startCamera}>
                      📷 Start Camera
                    </button>
                  </div>
                )}

                {cameraReady && (
                  <div className="capture-overlay">
                    <div className="capture-frame"></div>
                    <div className="capture-instructions">
                      <span>📐 Position ID card in frame</span>
                    </div>
                  </div>
                )}
              </div>

              {cameraReady && (
                <div className="camera-actions">
                  {isMobile && (
                    <button className="switch-camera-btn" onClick={switchCamera}>
                      🔄 Switch
                    </button>
                  )}
                  <button className="cancel-btn" onClick={closeCamera}>Cancel</button>
                  <button className="capture-btn" onClick={captureImage}>📸 Capture</button>
                </div>
              )}
            </div>
          )}

          {capturedImage && (
            <div className="captured-preview">
              <div className="captured-image-container">
                <img src={capturedImage} alt="Captured ID" className="captured-image" />
                {isSaving && (
                  <div className="saving-overlay">
                    <div className="spinner-small"></div>
                    <p>Saving to database...</p>
                  </div>
                )}
              </div>
              <div className="capture-actions">
                <button className="retake-btn" onClick={retakeImage} disabled={isSaving}>
                  🔄 Retake
                </button>
                <button className="confirm-save-btn" onClick={confirmAndSave} disabled={isSaving}>
                  {isSaving ? '💾 Saving...' : '💾 Confirm & Save'}
                </button>
              </div>
              <p className="save-hint">Image will be saved directly to database</p>
            </div>
          )}

          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
      </div>
    </div>
  );
};

export default CameraCapture;