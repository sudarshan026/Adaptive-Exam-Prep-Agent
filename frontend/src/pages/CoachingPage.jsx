import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function CoachingPage() {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => { fetchReport(); }, []);

  const fetchReport = async () => {
    try {
      const res = await api.get('/study/dashboard'); // Just use dashboard data for now to check if topics exist
      if (res.data.topics_total === 0) {
        setError('Please add topics to your syllabus and complete some sessions to generate a coaching report.');
        setLoading(false);
        return;
      }
      // If we had a specific coaching endpoint, we'd call it here
      // Let's generate one on the fly for the MVP
      generateReport();
    } catch (err) {
      setError('Failed to load data');
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    setError('');
    try {
      // In a real app, this would be a dedicated endpoint
      // For this MVP, we'll fetch analytics and weakness data to construct a report
      const [perfRes, weakRes] = await Promise.all([
        api.get('/analytics/performance'),
        api.get('/analytics/weakness-report'),
      ]);
      
      const perf = perfRes.data;
      const weak = weakRes.data;

      setReport({
        title: "Weekly AI Strategy Review",
        date: new Date().toLocaleDateString(),
        overall_status: perf.overall_accuracy >= 70 ? "On Track" : perf.overall_accuracy >= 50 ? "Needs Attention" : "At Risk",
        summary: `You have completed ${perf.total_assessments} assessments with an overall accuracy of ${perf.overall_accuracy.toFixed(0)}%. You've studied for ${perf.study_hours_total} hours.`,
        strengths: perf.strong_topics,
        weaknesses: perf.weak_topics,
        action_items: weak.recommendations.length > 0 ? weak.recommendations : [
          "Complete more practice assessments to identify weak areas.",
          "Ensure you are following the daily study plan.",
        ],
        motivation: perf.overall_accuracy >= 70 ? "Great job! Keep up the consistent effort." : "Don't get discouraged. Focus on your weak areas and you'll see improvement."
      });
    } catch (err) {
      setError('Failed to generate coaching report. Make sure you have completed some assessments.');
    } finally {
      setLoading(false);
      setGenerating(false);
    }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}><div className="spinner"></div></div>;

  return (
    <div className="page-container" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>🏆 AI Coaching Report</h1>
        <button className="btn-primary" onClick={generateReport} disabled={generating}>
          {generating ? '⏳ Generating...' : '🔄 Refresh Report'}
        </button>
      </div>

      {error ? (
        <div className="glass-card empty-state">
          <div className="empty-icon">📊</div>
          <h3>Not Enough Data</h3>
          <p>{error}</p>
          <button className="btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/practice')}>
            Take an Assessment
          </button>
        </div>
      ) : report ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="glass-card" style={{ background: 'radial-gradient(ellipse at top right, rgba(99, 102, 241, 0.15) 0%, var(--glass-bg) 60%)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{report.title}</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{report.date}</p>
              </div>
              <span className={`badge ${
                report.overall_status === 'On Track' ? 'badge-success' : 
                report.overall_status === 'Needs Attention' ? 'badge-warning' : 'badge-danger'
              }`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
                {report.overall_status}
              </span>
            </div>
            <p style={{ fontSize: '1.1rem', lineHeight: 1.6 }}>{report.summary}</p>
            <p style={{ fontSize: '1.1rem', lineHeight: 1.6, marginTop: '1rem', fontStyle: 'italic', color: 'var(--primary-light)' }}>
              "{report.motivation}"
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="glass-card">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                💪 Strengths to Maintain
              </h3>
              {report.strengths.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>Keep practicing to build your strengths.</p>
              ) : (
                <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-primary)' }}>
                  {report.strengths.map((s, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{s}</li>)}
                </ul>
              )}
            </div>
            <div className="glass-card">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⚠️ Weaknesses to Address
              </h3>
              {report.weaknesses.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No major weaknesses identified right now.</p>
              ) : (
                <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-primary)' }}>
                  {report.weaknesses.map((w, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{w}</li>)}
                </ul>
              )}
            </div>
          </div>

          <div className="glass-card" style={{ borderLeft: '4px solid var(--accent)' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              📋 Recommended Action Plan
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {report.action_items.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '8px' }}>
                  <span style={{ background: 'var(--accent)', color: 'white', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 700, flexShrink: 0 }}>
                    {i + 1}
                  </span>
                  <span style={{ fontSize: '0.95rem', lineHeight: 1.5 }}>{item}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button className="btn-primary" onClick={() => navigate('/study-plan')}>
                View Study Plan
              </button>
              <button className="btn-secondary" onClick={() => navigate('/tutor')}>
                Talk to AI Tutor
              </button>
            </div>
          </div>

        </div>
      ) : null}
    </div>
  );
}
