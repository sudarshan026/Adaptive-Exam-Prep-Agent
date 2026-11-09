import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts';
import api from '../services/api';

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [weakness, setWeakness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [remediating, setRemediating] = useState(false);
  const [remediationResult, setRemediationResult] = useState(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [perfRes, weakRes] = await Promise.all([
        api.get('/analytics/performance'),
        api.get('/analytics/weakness-report'),
      ]);
      setData(perfRes.data);
      setWeakness(weakRes.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const runParallelRemediation = async () => {
    setRemediating(true);
    try {
      const primaryWeak = weakness?.weak_topics?.[0]?.topic_name || data?.weak_topics?.[0] || 'General';
      const res = await api.post('/analytics/parallel-remediation', {
        topic_name: primaryWeak,
        daily_hours: 3.0,
        days_remaining: 45,
      });
      setRemediationResult(res.data);
    } catch (err) {
      alert('Failed to execute parallel remediation.');
    } finally {
      setRemediating(false);
    }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}><div className="spinner"></div></div>;
  if (!data) return <div className="page-container"><div className="glass-card">Failed to load analytics</div></div>;

  const chartStyle = { background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>📈 Performance Analytics</h1>
        <button
          className="btn-primary"
          onClick={runParallelRemediation}
          disabled={remediating}
          style={{ background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)', border: 'none', fontWeight: 600 }}
        >
          {remediating ? '⚡ Running 3 Agents in Parallel...' : '⚡ Multi-Agent Parallel Remediation'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid-stats" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--primary-light)' }}>{data.overall_accuracy.toFixed(0)}%</div>
          <div className="stat-label">Overall Accuracy</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--accent)' }}>{data.total_assessments}</div>
          <div className="stat-label">Assessments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--success)' }}>{data.total_correct}/{data.total_questions_attempted}</div>
          <div className="stat-label">Correct Answers</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--primary-light)' }}>{data.study_hours_total}h</div>
          <div className="stat-label">Study Hours</div>
        </div>
      </div>

      {/* Parallel Remediation Fan-Out / Fan-In Card */}
      {remediationResult && (
        <div className="glass-card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid #10b981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⚡ Multi-Agent Parallel Remediation Pipeline
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Concurrently executed: <strong>Weakness Detection</strong> ⚡ <strong>Resource Discovery</strong> ⚡ <strong>Coaching Advisor</strong> → Consolidated into <strong>Adaptive Planner</strong>.
              </p>
            </div>
            <span className="badge badge-success">
              Mode: {remediationResult.coordination_mode || 'fan_out_fan_in_parallel'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            {/* Weakness analysis branch */}
            <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'var(--bg-dark)', border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#ef4444', marginBottom: '0.4rem' }}>
                🔍 Weakness Diagnosis
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                {remediationResult.parallel_agent_outputs?.weakness_analysis?.overall_diagnosis || 'Identified root causes and targeted remediation areas.'}
              </p>
            </div>

            {/* Coaching branch */}
            <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'var(--bg-dark)', border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f59e0b', marginBottom: '0.4rem' }}>
                🏆 Coaching Insight
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                {remediationResult.parallel_agent_outputs?.coaching_message || 'Stay consistent and focus on understanding core principles.'}
              </p>
            </div>

            {/* Adaptive plan summary */}
            <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'var(--bg-dark)', border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#10b981', marginBottom: '0.4rem' }}>
                📅 Adapted Plan
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                {remediationResult.adapted_strategy?.adaptations?.summary || 'Reallocated hours to focus on high-yield topic improvements.'}
              </p>
            </div>
          </div>

          {/* Curated resources */}
          {remediationResult.parallel_agent_outputs?.discovered_resources?.length > 0 && (
            <div style={{ marginTop: '0.5rem', padding: '0.75rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.05)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--primary-light)' }}>
                📚 Concurrently Discovered Learning Resources
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {remediationResult.parallel_agent_outputs.discovered_resources.map((res, i) => (
                  <a
                    key={i}
                    href={res.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem', borderRadius: '6px', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--accent)', textDecoration: 'none' }}
                  >
                    🔗 {res.title}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Study Hours Chart */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📊 Study Hours (Last 30 Days)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.study_hours_by_day.filter(d => d.hours > 0)}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                tickFormatter={d => new Date(d).toLocaleDateString('en', { month: 'short', day: 'numeric' })} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={chartStyle} labelStyle={{ color: 'var(--text-primary)' }} />
              <Bar dataKey="hours" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Accuracy Trend */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>📈 Accuracy Trend</h2>
          {data.improvement_trend.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}><p>Complete assessments to see trends</p></div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data.improvement_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="title" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                <Tooltip contentStyle={chartStyle} />
                <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Topic Mastery */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>🎯 Topic Mastery</h2>
          {data.topic_mastery.length === 0 ? (
            <div className="empty-state" style={{ padding: '1.5rem' }}><p>Complete assessments to see mastery data</p></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {data.topic_mastery.map((m, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{m.topic_name}</span>
                    <span style={{ fontSize: '0.85rem', color: m.mastery_score >= 70 ? 'var(--success)' : m.mastery_score >= 50 ? 'var(--accent)' : 'var(--danger)' }}>
                      {m.mastery_score.toFixed(0)}%
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{
                      width: `${m.mastery_score}%`,
                      background: m.mastery_score >= 70 ? 'var(--success)' : m.mastery_score >= 50 ? 'var(--accent)' : 'var(--danger)',
                    }}></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weakness Report */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>⚠️ Weakness Analysis</h2>
          {weakness?.weak_topics.length === 0 ? (
            <div style={{ padding: '1.5rem', textAlign: 'center' }}>
              <span style={{ fontSize: '2rem' }}>✅</span>
              <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                {weakness?.insufficient_data_topics.length > 0
                  ? 'Not enough data yet. Complete more assessments.'
                  : 'No weak topics detected! Great job!'}
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {weakness.weak_topics.map((w, i) => (
                <div key={i} style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{w.topic_name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {w.subject_name} · Mastery: {w.mastery_score.toFixed(0)}% · {w.correct}/{w.total_attempted} correct
                  </div>
                </div>
              ))}
              {weakness.recommendations.length > 0 && (
                <div style={{ marginTop: '0.5rem', padding: '0.75rem', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.08)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>💡 Recommendations</div>
                  {weakness.recommendations.map((r, i) => (
                    <div key={i} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>• {r}</div>
                  ))}
                </div>
              )}
            </div>
          )}
          {weakness?.insufficient_data_topics.length > 0 && (
            <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              ℹ️ Insufficient data for: {weakness.insufficient_data_topics.join(', ')}
            </div>
          )}
        </div>
      </div>

      {/* Strong/Weak Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>💪 Strong Topics</h2>
          {data.strong_topics.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Keep practicing to build strong areas</p>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {data.strong_topics.map((t, i) => (
                <span key={i} className="badge badge-success">{t}</span>
              ))}
            </div>
          )}
        </div>
        <div className="glass-card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>🔴 Weak Topics</h2>
          {data.weak_topics.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No confirmed weak topics yet</p>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {data.weak_topics.map((t, i) => (
                <span key={i} className="badge badge-danger">{t}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
