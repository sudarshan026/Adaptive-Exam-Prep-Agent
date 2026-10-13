import { useState, useEffect } from 'react';
import api from '../services/api';

export default function ParentDashboardPage() {
  const [data, setData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [weakness, setWeakness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [dashRes, perfRes, predRes, weakRes] = await Promise.allSettled([
        api.get('/study/dashboard'),
        api.get('/analytics/performance'),
        api.get('/analytics/predicted-score'),
        api.get('/analytics/weakness-report'),
      ]);
      if (dashRes.status === 'fulfilled') setData({ ...dashRes.value.data, performance: perfRes.status === 'fulfilled' ? perfRes.value.data : null });
      if (predRes.status === 'fulfilled') setPrediction(predRes.value.data);
      if (weakRes.status === 'fulfilled') setWeakness(weakRes.value.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getGrade = (score) => {
    if (score >= 90) return { letter: 'A+', color: '#22c55e' };
    if (score >= 80) return { letter: 'A', color: '#22c55e' };
    if (score >= 70) return { letter: 'B', color: '#84cc16' };
    if (score >= 60) return { letter: 'C', color: '#f59e0b' };
    if (score >= 50) return { letter: 'D', color: '#f97316' };
    return { letter: 'F', color: '#ef4444' };
  };

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  if (!data) return (
    <div className="page-container" style={{ padding: '1.5rem' }}>
      <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>👨‍👩‍👦</p>
        <p style={{ color: 'var(--text-muted)' }}>Student needs to complete onboarding first.</p>
      </div>
    </div>
  );

  const perf = data.performance;
  const grade = prediction ? getGrade(prediction.predicted_score) : { letter: '?', color: '#6366f1' };

  return (
    <div className="page-container" style={{ padding: '1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
          👨‍👩‍👦 <span className="gradient-text">Parent / Teacher Dashboard</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Monitor {data.welcome_name}'s exam preparation progress
        </p>
      </div>

      {/* Quick Stats Banner */}
      <div className="glass-card" style={{
        padding: '1.5rem', marginBottom: '1.5rem',
        background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))',
        display: 'flex', flexWrap: 'wrap', gap: '1.5rem', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Student</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{data.welcome_name}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{data.exam_type} • {data.days_remaining != null ? `${data.days_remaining} days left` : 'No exam date set'}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 70, height: 70, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: `${grade.color}22`, border: `3px solid ${grade.color}`,
            fontSize: '1.5rem', fontWeight: 800, color: grade.color,
          }}>
            {grade.letter}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Predicted Grade</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {[
          { key: 'overview', label: '📊 Overview' },
          { key: 'progress', label: '📈 Progress' },
          { key: 'weaknesses', label: '⚠️ Weak Areas' },
          { key: 'activity', label: '📅 Activity' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '0.5rem 1rem', borderRadius: '8px 8px 0 0', border: 'none', cursor: 'pointer',
              background: activeTab === tab.key ? 'rgba(99,102,241,0.15)' : 'transparent',
              color: activeTab === tab.key ? 'var(--primary-light)' : 'var(--text-muted)',
              fontWeight: activeTab === tab.key ? 700 : 400, fontSize: '0.85rem',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { label: 'Overall Progress', value: `${data.overall_progress?.toFixed(0) || 0}%`, icon: '📊', color: '#6366f1' },
              { label: 'Study Streak', value: `${data.study_streak || 0} days`, icon: '🔥', color: '#f59e0b' },
              { label: 'Total Study Hours', value: `${data.total_study_hours || 0}h`, icon: '⏱️', color: '#22c55e' },
              { label: 'Topics Completed', value: `${data.topics_completed || 0}/${data.topics_total || 0}`, icon: '✅', color: '#8b5cf6' },
              { label: 'Predicted Score', value: prediction ? `${prediction.predicted_score}%` : 'N/A', icon: '🎯', color: '#06b6d4' },
              { label: 'Hours Today', value: `${data.completed_hours_today || 0}h`, icon: '📖', color: '#ec4899' },
            ].map((stat, i) => (
              <div key={i} className="glass-card" style={{ padding: '1.25rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{stat.icon}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Mastery Overview */}
          {data.mastery_summary && data.mastery_summary.length > 0 && (
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>📋 Topic Mastery Overview</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.mastery_summary.slice(0, 12).map((m, i) => {
                  const color = m.mastery_score >= 70 ? '#22c55e' : m.mastery_score >= 40 ? '#f59e0b' : '#ef4444';
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '0.8rem', minWidth: '150px', color: 'var(--text-secondary)' }}>{m.topic_name}</span>
                      <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.06)' }}>
                        <div style={{ width: `${m.mastery_score}%`, height: '100%', borderRadius: 4, background: color, transition: 'width 0.5s' }} />
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color, minWidth: '40px', textAlign: 'right' }}>{m.mastery_score.toFixed(0)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {activeTab === 'progress' && (
        <>
          {prediction && (
            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>🎯 Score Prediction Breakdown</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {[
                  { label: 'Mastery (40%)', value: prediction.breakdown.mastery_component.toFixed(1), max: 40 },
                  { label: 'Assessments (30%)', value: prediction.breakdown.assessment_component.toFixed(1), max: 30 },
                  { label: 'Coverage (20%)', value: prediction.breakdown.coverage_component.toFixed(1), max: 20 },
                  { label: 'Consistency (10%)', value: prediction.breakdown.consistency_component.toFixed(1), max: 10 },
                ].map((item, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                      <span style={{ fontWeight: 700 }}>{item.value}/{item.max}</span>
                    </div>
                    <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.08)' }}>
                      <div style={{ width: `${(parseFloat(item.value) / item.max) * 100}%`, height: '100%', borderRadius: 4, background: 'linear-gradient(90deg, var(--primary), var(--accent))' }} />
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', fontSize: '0.8rem' }}>
                <span>📈 Trend: <strong style={{ textTransform: 'capitalize' }}>{prediction.trend}</strong></span>
                <span>🔒 Confidence: <strong style={{ textTransform: 'capitalize' }}>{prediction.confidence}</strong></span>
              </div>
            </div>
          )}

          {/* Recent Assessments */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>📝 Recent Assessment Results</h3>
            {data.recent_assessments && data.recent_assessments.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.recent_assessments.map((a, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem', borderRadius: '10px', background: 'rgba(255,255,255,0.03)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{a.title}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{a.topic_name}</div>
                    </div>
                    <div style={{
                      fontWeight: 800, fontSize: '1rem',
                      color: a.accuracy >= 70 ? '#22c55e' : a.accuracy >= 50 ? '#f59e0b' : '#ef4444',
                    }}>
                      {a.accuracy?.toFixed(0) || a.score}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No assessments completed yet.</p>
            )}
          </div>
        </>
      )}

      {activeTab === 'weaknesses' && (
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>⚠️ Areas Needing Attention</h3>
          {weakness && weakness.weak_topics && weakness.weak_topics.length > 0 ? (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
                {weakness.weak_topics.map((w, i) => (
                  <div key={i} style={{
                    padding: '1rem', borderRadius: '10px',
                    background: 'rgba(239,68,68,0.08)', borderLeft: '3px solid #ef4444',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                      <strong style={{ fontSize: '0.9rem' }}>{w.topic_name}</strong>
                      <span style={{ fontWeight: 800, color: '#ef4444' }}>{w.mastery_score?.toFixed(0) || w.accuracy?.toFixed(0)}%</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {w.subject_name} • {w.total_attempted || 0} questions attempted • Confidence: {w.confidence_level || 'low'}
                    </div>
                  </div>
                ))}
              </div>
              {weakness.recommendations && (
                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem' }}>💡 Recommendations</h4>
                  <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    {weakness.recommendations.map((r, i) => (
                      <li key={i} style={{ marginBottom: '0.25rem' }}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎉</p>
              <p style={{ color: 'var(--text-muted)' }}>
                {weakness?.insufficient_data_topics?.length > 0
                  ? `Need more data. Topics with insufficient attempts: ${weakness.insufficient_data_topics.join(', ')}`
                  : 'No significant weaknesses detected! Great progress!'}
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'activity' && (
        <>
          {/* Today's Schedule */}
          <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>📅 Today's Study Sessions</h3>
            {data.today_sessions && data.today_sessions.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.today_sessions.map((s, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem', borderRadius: '10px', background: 'rgba(255,255,255,0.03)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{s.topic_name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.session_type} • {s.estimated_duration_minutes}min</div>
                    </div>
                    <span style={{
                      padding: '3px 10px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 600,
                      background: s.status === 'completed' ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.15)',
                      color: s.status === 'completed' ? '#22c55e' : '#f59e0b',
                    }}>
                      {s.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No sessions scheduled for today.</p>
            )}
          </div>

          {/* Upcoming */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>📋 Upcoming Sessions</h3>
            {data.upcoming_sessions && data.upcoming_sessions.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.upcoming_sessions.map((s, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem', borderRadius: '10px', background: 'rgba(255,255,255,0.03)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{s.topic_name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.session_type} • {s.scheduled_date}</div>
                    </div>
                    <span style={{
                      padding: '3px 10px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 600,
                      background: 'rgba(99,102,241,0.15)', color: 'var(--primary-light)',
                    }}>
                      {s.estimated_duration_minutes}min
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No upcoming sessions.</p>
            )}
          </div>
        </>
      )}

      {/* Footer Note */}
      <div style={{
        marginTop: '1.5rem', padding: '1rem', borderRadius: '10px',
        background: 'rgba(99,102,241,0.06)', textAlign: 'center',
        fontSize: '0.75rem', color: 'var(--text-muted)',
      }}>
        📊 This dashboard provides a read-only view of the student's progress. Data updates in real time as the student studies.
      </div>
    </div>
  );
}
