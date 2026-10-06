import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/profile/');
      setProfile(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      await api.put('/profile/', profile);
      setMessage('Settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}><div className="spinner"></div></div>;

  return (
    <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 className="page-title">⚙️ Settings</h1>
      
      {message && (
        <div style={{
          background: message.includes('success') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: '1px solid',
          borderColor: message.includes('success') ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
          borderRadius: '10px', padding: '1rem', marginBottom: '1.5rem',
          color: message.includes('success') ? 'var(--success)' : 'var(--danger)',
        }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Account Info */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Account Information</h2>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label className="form-label">Full Name</label>
              <input type="text" className="input-field" value={user?.full_name || ''} disabled />
            </div>
            <div style={{ flex: 1 }}>
              <label className="form-label">Username</label>
              <input type="text" className="input-field" value={user?.username || ''} disabled />
            </div>
          </div>
          <div>
            <label className="form-label">Email</label>
            <input type="email" className="input-field" value={user?.email || ''} disabled />
          </div>
        </div>

        {/* Study Preferences */}
        {profile && (
          <form onSubmit={handleSave} className="glass-card">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Study Preferences</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label className="form-label">Exam Type</label>
                <input type="text" className="input-field" value={profile.exam_type} 
                  onChange={e => setProfile({...profile, exam_type: e.target.value})} required />
              </div>
              <div>
                <label className="form-label">Target Score</label>
                <input type="number" className="input-field" value={profile.target_score || ''} 
                  onChange={e => setProfile({...profile, target_score: e.target.value ? parseFloat(e.target.value) : null})} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label className="form-label">Current Level</label>
                <select className="input-field" value={profile.current_level} 
                  onChange={e => setProfile({...profile, current_level: e.target.value})}>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
              <div>
                <label className="form-label">Learning Preference</label>
                <select className="input-field" value={profile.learning_preference} 
                  onChange={e => setProfile({...profile, learning_preference: e.target.value})}>
                  <option value="visual">Visual</option>
                  <option value="reading">Reading</option>
                  <option value="practice">Practice</option>
                  <option value="balanced">Balanced</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label className="form-label">Daily Study Hours: {profile.daily_study_hours}h</label>
                <input type="range" min="0.5" max="12" step="0.5" className="input-field" style={{ padding: '0' }}
                  value={profile.daily_study_hours} 
                  onChange={e => setProfile({...profile, daily_study_hours: parseFloat(e.target.value)})} />
              </div>
              <div>
                <label className="form-label">Exam Date</label>
                <input type="date" className="input-field" 
                  value={profile.exam_date ? profile.exam_date.split('T')[0] : ''} 
                  onChange={e => setProfile({...profile, exam_date: e.target.value})} />
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? '⏳ Saving...' : '💾 Save Changes'}
            </button>
          </form>
        )}

        {/* Danger Zone */}
        <div className="glass-card" style={{ border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', color: 'var(--danger)' }}>Danger Zone</h2>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p style={{ fontWeight: 500 }}>Sign Out</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Log out of your account on this device.</p>
            </div>
            <button className="btn-secondary" style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }} onClick={logout}>
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
