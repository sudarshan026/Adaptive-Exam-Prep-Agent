import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../services/api';

const MASTERY_COLORS = ['#ef4444', '#f59e0b', '#10b981', '#6366f1'];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/study/dashboard');
      setData(res.data);
    } catch (err) {
      if (err.response?.status === 404) {
        navigate('/onboarding');
        return;
      }
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const markComplete = async (sessionId) => {
    try {
      await api.put(`/study/sessions/${sessionId}`, { status: 'completed' });
      fetchDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
      <div className="spinner"></div>
    </div>
  );

  if (error) return (
    <div className="page-container">
      <div className="glass-card" style={{ textAlign: 'center', color: 'var(--danger)' }}>{error}</div>
    </div>
  );

  if (!data) return null;

  const progressPercent = Math.min(100, (data.completed_hours_today / data.daily_target_hours) * 100);

  // Mastery distribution for pie chart
  const masteryDist = [
    { name: 'Weak (<50%)', value: data.mastery_summary.filter(m => m.mastery_score < 50).length, color: '#ef4444' },
    { name: 'Medium (50-70%)', value: data.mastery_summary.filter(m => m.mastery_score >= 50 && m.mastery_score < 70).length, color: '#f59e0b' },
    { name: 'Good (70-90%)', value: data.mastery_summary.filter(m => m.mastery_score >= 70 && m.mastery_score < 90).length, color: '#10b981' },
    { name: 'Mastered (90%+)', value: data.mastery_summary.filter(m => m.mastery_score >= 90).length, color: '#6366f1' },
  ].filter(d => d.value > 0);

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
          Welcome back, <span className="gradient-text">{data.welcome_name}</span>! 👋
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          {data.exam_type} Preparation
          {data.days_remaining !== null && ` — ${data.days_remaining} days remaining`}
          {data.is_demo_mode && <span className="badge badge-warning" style={{ marginLeft: '0.75rem' }}>Demo Mode</span>}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid-stats" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>📅</div>
          <div className="stat-value" style={{ color: 'var(--primary-light)' }}>{data.days_remaining ?? '—'}</div>
          <div className="stat-label">Days Remaining</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>🔥</div>
          <div className="stat-value" style={{ color: 'var(--accent)' }}>{data.study_streak}</div>
          <div className="stat-label">Day Streak</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>⏱️</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{data.total_study_hours}h</div>
          <div className="stat-label">Total Study Hours</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>📊</div>
          <div className="stat-value" style={{ color: 'var(--primary-light)' }}>{data.overall_progress.toFixed(0)}%</div>
          <div className="stat-label">Overall Progress</div>
        </div>
      </div>

      {/* Today's Progress & Plan */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Today's Progress */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📈 Today's Progress</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{data.completed_hours_today}h</div>
            <span style={{ color: 'var(--text-muted)' }}>/ {data.daily_target_hours}h target</span>
          </div>
          <div className="progress-bar" style={{ marginBottom: '0.5rem' }}>
            <div className="progress-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {progressPercent >= 100 ? '🎉 Daily target achieved!' : `${(data.daily_target_hours - data.completed_hours_today).toFixed(1)}h remaining`}
          </span>
        </div>

        {/* Topics Progress */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📚 Topics Progress</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{data.topics_completed}</div>
            <span style={{ color: 'var(--text-muted)' }}>/ {data.topics_total} topics completed</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ 
              width: `${data.topics_total > 0 ? (data.topics_completed / data.topics_total * 100) : 0}%`,
              background: 'linear-gradient(90deg, var(--success), #34d399)',
            }}></div>
          </div>
          {data.topics_total === 0 && (
            <button className="btn-primary" style={{ marginTop: '1rem', fontSize: '0.85rem', padding: '0.5rem 1rem' }}
              onClick={() => navigate('/syllabus')}>
              + Add Your Syllabus
            </button>
          )}
        </div>
      </div>

      {/* Today's Study Plan & Weak Topics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Today's Sessions */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📋 Today's Study Plan</h2>
          {data.today_sessions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📅</div>
              <h3>No sessions scheduled for today</h3>
              <p>Generate a study plan to get started</p>
              <button className="btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/study-plan')}>
                Generate Plan
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {data.today_sessions.map(session => (
                <div key={session.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '0.75rem 1rem', borderRadius: '10px',
                  background: session.status === 'completed' ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-dark)',
                  border: '1px solid',
                  borderColor: session.status === 'completed' ? 'rgba(16, 185, 129, 0.3)' : 'var(--border)',
                  opacity: session.status === 'completed' ? 0.7 : 1,
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      {session.topic_name}
                      <span className={`badge ${
                        session.session_type === 'learning' ? 'badge-primary' : 
                        session.session_type === 'practice' ? 'badge-warning' : 
                        session.session_type === 'revision' ? 'badge-success' : 'badge-danger'
                      }`} style={{ marginLeft: '0.5rem' }}>
                        {session.session_type}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      {session.subject_name} · {session.estimated_duration_minutes}min · {session.priority} priority
                    </div>
                  </div>
                  {session.status !== 'completed' && (
                    <button className="btn-success" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                      onClick={() => markComplete(session.id)}>
                      ✓ Done
                    </button>
                  )}
                  {session.status === 'completed' && <span style={{ color: 'var(--success)' }}>✓</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weak Topics */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>⚠️ Weak Topics</h2>
          {data.weak_topics.length === 0 ? (
            <div className="empty-state" style={{ padding: '1.5rem' }}>
              <p style={{ fontSize: '0.9rem' }}>No weak topics identified yet. Complete some assessments first!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {data.weak_topics.map((wt, i) => (
                <div key={i} style={{
                  padding: '0.75rem', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{wt.topic_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {wt.subject_name} · Mastery: {wt.mastery_score?.toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Mastery Chart & Recent Assessments */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Mastery Pie */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>🎯 Topic Mastery Distribution</h2>
          {masteryDist.length === 0 ? (
            <div className="empty-state" style={{ padding: '1.5rem' }}>
              <p>Complete assessments to see mastery data</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={masteryDist} dataKey="value" nameKey="name" cx="50%" cy="50%"
                  innerRadius={50} outerRadius={80} paddingAngle={4}>
                  {masteryDist.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center', marginTop: '0.5rem' }}>
            {masteryDist.map((d, i) => (
              <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: d.color }}></span>
                {d.name} ({d.value})
              </span>
            ))}
          </div>
        </div>

        {/* Recent Assessments */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📝 Recent Assessments</h2>
          {data.recent_assessments.length === 0 ? (
            <div className="empty-state" style={{ padding: '1.5rem' }}>
              <p>No assessments completed yet</p>
              <button className="btn-primary" style={{ marginTop: '1rem', fontSize: '0.85rem' }}
                onClick={() => navigate('/practice')}>
                Start Practice
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {data.recent_assessments.map(a => (
                <div key={a.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.75rem', borderRadius: '8px', background: 'var(--bg-dark)',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{a.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{a.topic_name}</div>
                  </div>
                  <span className={`badge ${a.accuracy >= 70 ? 'badge-success' : a.accuracy >= 50 ? 'badge-warning' : 'badge-danger'}`}>
                    {a.accuracy?.toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
