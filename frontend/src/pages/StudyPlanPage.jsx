import { useState, useEffect } from 'react';
import api from '../services/api';

export default function StudyPlanPage() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [view, setView] = useState('daily'); // daily, weekly
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => { fetchPlan(); }, []);

  const fetchPlan = async () => {
    try {
      const res = await api.get('/study/plan');
      setPlan(res.data);
    } catch (err) {
      if (err.response?.status !== 404) console.error(err);
    }
    finally { setLoading(false); }
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const res = await api.post('/study/generate-plan', { force_regenerate: true });
      setPlan(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate plan. Add subjects & topics first.');
    } finally { setGenerating(false); }
  };

  const markComplete = async (sessionId) => {
    try {
      await api.put(`/study/sessions/${sessionId}`, { status: 'completed' });
      fetchPlan();
    } catch (err) { console.error(err); }
  };

  const getSessionsByDate = () => {
    if (!plan?.sessions) return {};
    const grouped = {};
    plan.sessions.forEach(s => {
      if (!grouped[s.scheduled_date]) grouped[s.scheduled_date] = [];
      grouped[s.scheduled_date].push(s);
    });
    return grouped;
  };

  const sessionsByDate = getSessionsByDate();
  const dates = Object.keys(sessionsByDate).sort();
  const today = new Date().toISOString().split('T')[0];

  // Filter for daily/weekly view
  const getVisibleDates = () => {
    if (view === 'daily') return dates.filter(d => d === selectedDate);
    const sel = new Date(selectedDate);
    const weekStart = new Date(sel);
    weekStart.setDate(sel.getDate() - sel.getDay());
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    return dates.filter(d => d >= weekStart.toISOString().split('T')[0] && d <= weekEnd.toISOString().split('T')[0]);
  };

  const typeIcon = { learning: '📖', practice: '✏️', revision: '🔄', assessment: '📝' };
  const priorityColor = { critical: 'var(--danger)', high: 'var(--accent)', medium: 'var(--primary-light)', low: 'var(--text-muted)' };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}><div className="spinner"></div></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: '0.25rem' }}>📅 Study Plan</h1>
          {plan && <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Version {plan.version} · {plan.sessions?.length || 0} sessions
            {plan.change_reason && ` · ${plan.change_reason}`}
          </p>}
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input type="date" className="input-field" style={{ width: '160px' }}
            value={selectedDate} onChange={e => setSelectedDate(e.target.value)} />
          <div style={{ display: 'flex', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border)' }}>
            {['daily', 'weekly'].map(v => (
              <button key={v} onClick={() => setView(v)} style={{
                padding: '0.5rem 1rem', border: 'none', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500,
                background: view === v ? 'var(--primary)' : 'var(--bg-card)', color: view === v ? 'white' : 'var(--text-secondary)',
              }}>{v.charAt(0).toUpperCase() + v.slice(1)}</button>
            ))}
          </div>
          <button className="btn-primary" onClick={generatePlan} disabled={generating}>
            {generating ? '⏳ Generating...' : plan ? '🔄 Regenerate' : '📅 Generate Plan'}
          </button>
        </div>
      </div>

      {!plan ? (
        <div className="glass-card empty-state">
          <div className="empty-icon">📅</div>
          <h3>No Study Plan Yet</h3>
          <p>Add subjects and topics to your syllabus, then generate a personalized study plan</p>
          <button className="btn-primary" style={{ marginTop: '1rem' }} onClick={generatePlan} disabled={generating}>
            {generating ? 'Generating...' : '📅 Generate Plan'}
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Stats */}
          <div className="grid-stats">
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--primary-light)' }}>{plan.sessions?.length || 0}</div>
              <div className="stat-label">Total Sessions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--success)' }}>
                {plan.sessions?.filter(s => s.status === 'completed').length || 0}
              </div>
              <div className="stat-label">Completed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--accent)' }}>
                {plan.sessions?.filter(s => s.status === 'pending' && s.scheduled_date < today).length || 0}
              </div>
              <div className="stat-label">Overdue</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--text-secondary)' }}>
                {dates.length}
              </div>
              <div className="stat-label">Study Days</div>
            </div>
          </div>

          {/* Sessions by date */}
          {getVisibleDates().length === 0 ? (
            <div className="glass-card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
              No sessions scheduled for {view === 'daily' ? 'this date' : 'this week'}
            </div>
          ) : (
            getVisibleDates().map(dateStr => (
              <div key={dateStr} className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontWeight: 600 }}>
                    {dateStr === today ? '📌 Today' : new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                    {dateStr < today && dateStr !== today && <span className="badge badge-warning" style={{ marginLeft: '0.5rem' }}>Past</span>}
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {sessionsByDate[dateStr].reduce((sum, s) => sum + s.estimated_duration_minutes, 0)} min total
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {sessionsByDate[dateStr].map(session => (
                    <div key={session.id} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.75rem 1rem', borderRadius: '10px',
                      background: session.status === 'completed' ? 'rgba(16, 185, 129, 0.08)' : 'var(--bg-dark)',
                      border: '1px solid',
                      borderColor: session.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : 'var(--border)',
                      borderLeft: `3px solid ${priorityColor[session.priority] || 'var(--border)'}`,
                      textDecoration: session.status === 'completed' ? 'none' : 'none',
                      opacity: session.status === 'completed' ? 0.7 : 1,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '1.25rem' }}>{typeIcon[session.session_type] || '📖'}</span>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{session.topic_name}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '0.75rem', marginTop: '0.15rem' }}>
                            <span>{session.subject_name}</span>
                            <span>{session.estimated_duration_minutes}min</span>
                            <span className={`badge ${
                              session.session_type === 'learning' ? 'badge-primary' :
                              session.session_type === 'practice' ? 'badge-warning' :
                              session.session_type === 'revision' ? 'badge-success' : 'badge-danger'
                            }`}>{session.session_type}</span>
                          </div>
                        </div>
                      </div>
                      {session.status === 'completed' ? (
                        <span style={{ color: 'var(--success)', fontWeight: 600, fontSize: '0.85rem' }}>✓ Done</span>
                      ) : (
                        <button className="btn-success" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => markComplete(session.id)}>
                          Complete
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
