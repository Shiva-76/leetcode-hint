import React, { useEffect, useState } from 'react';

export default function Options() {
  const [backendUrl, setBackendUrl] = useState('ws://localhost:8000/ws/coach');
  const [authToken, setAuthToken] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    chrome.storage.local.get(['backendUrl', 'authToken'], (res) => {
      if (res.backendUrl) setBackendUrl(res.backendUrl);
      if (res.authToken) setAuthToken(res.authToken);
    });
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    chrome.storage.local.set({ backendUrl, authToken }, () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    });
  };

  return (
    <div style={{ maxWidth: '500px', margin: '40px auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', color: '#1f2937' }}>
        LeetCode Coach Configuration
      </h1>
      
      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#4b5563' }}>
            Backend Server URL
          </label>
          <input
            type="text"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '10px', 
              borderRadius: '6px', 
              border: '1px solid #d1d5db',
              fontSize: '14px'
            }}
            placeholder="ws://your-ec2-ip:8000/ws/coach"
          />
          <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            The WebSocket URL of your backend. For local dev, use <code>ws://localhost:8000/ws/coach</code>.
          </p>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#4b5563' }}>
            Authentication Token (Optional)
          </label>
          <input
            type="password"
            value={authToken}
            onChange={(e) => setAuthToken(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '10px', 
              borderRadius: '6px', 
              border: '1px solid #d1d5db',
              fontSize: '14px'
            }}
            placeholder="Your secret token"
          />
          <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            Must match <code>SERVER_AUTH_TOKEN</code> in your backend .env file.
          </p>
        </div>

        <button 
          type="submit" 
          style={{
            padding: '12px',
            backgroundColor: '#4f46e5',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px'
          }}
        >
          {saved ? 'Saved!' : 'Save Configuration'}
        </button>

      </form>
    </div>
  );
}
