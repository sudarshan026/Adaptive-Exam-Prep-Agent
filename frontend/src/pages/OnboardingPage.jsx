import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const EXAM_TYPES = ['GATE CSE', 'GATE ECE', 'JEE Main', 'JEE Advanced', 'NEET', 'CAT', 'UPSC', 'GRE', 'Custom'];
const LEVELS = ['beginner', 'intermediate', 'advanced'];
const PREFERENCES = [
  { value: 'visual', label: '🎨 Visual — Diagrams & videos' },
  { value: 'reading', label: '📖 Reading — Text & notes' },
  { value: 'practice', label: '✏️ Practice — Problems & exercises' },
  { value: 'balanced', label: '⚖️ Balanced — Mix of all styles' },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    exam_type: '', target_score: '', current_level: 'intermediate',
    exam_date: '', daily_study_hours: 4,
    learning_preference: 'balanced',
    strong_topics: '', weak_topics: '',
  });

  const totalSteps = 3;
  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    setError('');
    setLoading(true);
    try {
      const payload = {
        ...form,
        target_score: form.target_score ? parseFloat(form.target_score) : null,
        daily_study_hours: parseFloat(form.daily_study_hours),
        exam_date: form.exam_date || null,
        strong_topics: form.strong_topics ? form.strong_topics.split(',').map(s => s.trim()).filter(Boolean) : [],
        weak_topics: form.weak_topics ? form.weak_topics.split(',').map(s => s.trim()).filter(Boolean) : [],
      };
      await api.post('/profile/', payload);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.1) 0%, var(--bg-dark) 60%)',
      padding: '2rem',
    }}>
      <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '550px' }}>
        {/* Progress */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
          {[1, 2, 3].map(s => (
            <div key={s} style={{
              flex: 1, height: '4px', borderRadius: '2px',
              background: s <= step ? 'var(--primary)' : 'var(--border)',
              transition: 'background 0.3s ease',
            }} />
          ))}
        </div>

        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          {step === 1 && '📋 Exam Details'}
          {step === 2 && '⏰ Study Schedule'}
          {step === 3 && '📊 Your Strengths & Weaknesses'}
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Step {step} of {totalSteps} — {step === 1 ? 'Tell us about your exam' : step === 2 ? 'Set up your study schedule' : 'Help us personalize your plan'}
        </p>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px', padding: '0.75rem 1rem', marginBottom: '1.25rem',
            color: 'var(--danger)', fontSize: '0.85rem',
          }}>{error}</div>
        )}

        {/* Step 1: Exam Details */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label className="form-label">Exam Type *</label>
              <select className="input-field" value={form.exam_type} onChange={e => update('exam_type', e.target.value)} required>
                <option value="">Select your exam</option>
                {EXAM_TYPES.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Target Score (optional)</label>
              <input type="number" className="input-field" placeholder="e.g., 85"
                value={form.target_score} onChange={e => update('target_score', e.target.value)} />
            </div>
            <div>
              <label className="form-label">Current Level</label>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                {LEVELS.map(l => (
                  <button key={l} type="button"
                    onClick={() => update('current_level', l)}
                    style={{
                      flex: 1, padding: '0.6rem', borderRadius: '10px', border: '1px solid',
                      borderColor: form.current_level === l ? 'var(--primary)' : 'var(--border)',
                      background: form.current_level === l ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                      color: form.current_level === l ? 'var(--primary-light)' : 'var(--text-secondary)',
                      cursor: 'pointer', fontWeight: 500, fontSize: '0.85rem', textTransform: 'capitalize',
                    }}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Schedule */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label className="form-label">Exam Date</label>
              <input type="date" className="input-field"
                value={form.exam_date} onChange={e => update('exam_date', e.target.value)}
                min={new Date().toISOString().split('T')[0]} />
            </div>
            <div>
              <label className="form-label">Daily Study Hours: {form.daily_study_hours}h</label>
              <input type="range" min="0.5" max="12" step="0.5"
                value={form.daily_study_hours} onChange={e => update('daily_study_hours', e.target.value)}
                style={{ width: '100%', accentColor: 'var(--primary)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span>0.5h</span><span>12h</span>
              </div>
            </div>
            <div>
              <label className="form-label">Learning Preference</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {PREFERENCES.map(p => (
                  <button key={p.value} type="button"
                    onClick={() => update('learning_preference', p.value)}
                    style={{
                      padding: '0.75rem 1rem', borderRadius: '10px', border: '1px solid',
                      borderColor: form.learning_preference === p.value ? 'var(--primary)' : 'var(--border)',
                      background: form.learning_preference === p.value ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                      color: form.learning_preference === p.value ? 'var(--primary-light)' : 'var(--text-secondary)',
                      cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem', textAlign: 'left',
                    }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Strengths/Weaknesses */}
        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label className="form-label">Strong Subjects/Topics (comma-separated)</label>
              <input type="text" className="input-field" placeholder="e.g., DBMS, Operating Systems"
                value={form.strong_topics} onChange={e => update('strong_topics', e.target.value)} />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Topics you feel confident about</span>
            </div>
            <div>
              <label className="form-label">Weak Subjects/Topics (comma-separated)</label>
              <input type="text" className="input-field" placeholder="e.g., Computer Networks, TOC"
                value={form.weak_topics} onChange={e => update('weak_topics', e.target.value)} />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Topics you struggle with — these will be prioritized</span>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          {step > 1 && (
            <button className="btn-secondary" onClick={() => setStep(step - 1)} style={{ flex: 1 }}>
              ← Back
            </button>
          )}
          {step < totalSteps ? (
            <button className="btn-primary" onClick={() => {
              if (step === 1 && !form.exam_type) { setError('Please select an exam type'); return; }
              setError('');
              setStep(step + 1);
            }} style={{ flex: 1, justifyContent: 'center' }}>
              Next →
            </button>
          ) : (
            <button className="btn-primary" onClick={handleSubmit} disabled={loading}
              style={{ flex: 1, justifyContent: 'center' }}>
              {loading ? 'Saving...' : '🎯 Complete Setup'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
