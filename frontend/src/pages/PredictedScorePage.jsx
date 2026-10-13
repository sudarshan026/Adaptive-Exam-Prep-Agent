import { useState, useEffect } from 'react';
import api from '../services/api';

export default function PredictedScorePage() {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { fetchPrediction(); }, []);

  const fetchPrediction = async () => {
    try {
      const res = await api.get('/analytics/predicted-score');
      setPrediction(res.data);
    } catch (err) {
      setError('Complete some assessments first to see your predicted score.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#f97316';
    return '#ef4444';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'improving') return '📈';
    if (trend === 'declining') return '📉';
    return '➡️';
  };

  const getConfidenceBadge = (conf) => {
    const colors = { high: '#22c55e', medium: '#f59e0b', low: '#ef4444' };
    return {
      background: `${colors[conf] || '#6366f1'}22`,
      color: colors[conf] || '#6366f1',
      padding: '4px 12px',
      borderRadius: '20px',
      fontSize: '0.75rem',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    };
  };

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
          🎯 <span className="gradient-text">Predicted Exam Score</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          AI-powered prediction based on your mastery, assessments, and study habits
        </p>
      </div>

      {error ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <p style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📊</p>
          <p style={{ color: 'var(--text-muted)' }}>{error}</p>
        </div>
      ) : prediction && (
        <>
          {/* Main Score Card */}
          <div className="glass-card" style={{
            padding: '2.5rem',
            textAlign: 'center',
            marginBottom: '1.5rem',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1))',
          }}>
            <div style={{ position: 'relative', display: 'inline-block', marginBottom: '1rem' }}>
              {/* Circular score indicator */}
              <svg width="200" height="200" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="85" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="12" />
                <circle
                  cx="100" cy="100" r="85" fill="none"
                  stroke={getScoreColor(prediction.predicted_score)}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={`${(prediction.predicted_score / 100) * 534} 534`}
                  transform="rotate(-90 100 100)"
                  style={{ transition: 'stroke-dasharray 1.5s ease' }}
                />
                <text x="100" y="90" textAnchor="middle" fill="white" fontSize="42" fontWeight="800">
                  {prediction.predicted_score}
                </text>
                <text x="100" y="118" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="14" fontWeight="500">
                  out of 100
                </text>
              </svg>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
              <span style={getConfidenceBadge(prediction.confidence)}>
                Confidence: {prediction.confidence}
              </span>
              <span style={{
                padding: '4px 12px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700,
                background: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)',
              }}>
                {getTrendIcon(prediction.trend)} Trend: {prediction.trend}
              </span>
            </div>
          </div>

          {/* Score Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { label: 'Mastery Component', value: prediction.breakdown.mastery_component, max: 40, icon: '🧠', desc: '40% weight' },
              { label: 'Assessment Component', value: prediction.breakdown.assessment_component, max: 30, icon: '📝', desc: '30% weight' },
              { label: 'Coverage Component', value: prediction.breakdown.coverage_component, max: 20, icon: '📚', desc: '20% weight' },
              { label: 'Consistency Component', value: prediction.breakdown.consistency_component, max: 10, icon: '🔥', desc: '10% weight' },
            ].map((item, i) => (
              <div key={i} className="glass-card" style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '1.25rem' }}>{item.icon}</span>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '8px' }}>{item.desc}</span>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary-light)' }}>{item.value.toFixed(1)}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>{item.label}</div>
                <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.08)' }}>
                  <div style={{
                    width: `${(item.value / item.max) * 100}%`,
                    height: '100%', borderRadius: 3,
                    background: 'linear-gradient(90deg, var(--primary), var(--accent))',
                    transition: 'width 1s ease',
                  }} />
                </div>
              </div>
            ))}
          </div>

          {/* Detailed Factors */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>📋 Contributing Factors</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              {[
                { label: 'Average Mastery', value: `${prediction.factors.avg_mastery}%`, icon: '🧠' },
                { label: 'Recent Accuracy', value: `${prediction.factors.avg_recent_accuracy}%`, icon: '🎯' },
                { label: 'Topic Coverage', value: `${prediction.factors.topic_coverage}%`, icon: '📖' },
                { label: 'Study Streak', value: `${prediction.factors.study_streak} days`, icon: '🔥' },
                { label: 'Total Study Hours', value: `${prediction.factors.total_study_hours}h`, icon: '⏱️' },
                { label: 'Assessments Done', value: prediction.factors.assessments_completed, icon: '✅' },
                { label: 'Topics Assessed', value: `${prediction.factors.topics_assessed}/${prediction.factors.total_topics}`, icon: '📊' },
              ].map((f, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '0.75rem',
                  padding: '0.75rem', borderRadius: '10px', background: 'rgba(255,255,255,0.03)',
                }}>
                  <span style={{ fontSize: '1.25rem' }}>{f.icon}</span>
                  <div>
                    <div style={{ fontSize: '1rem', fontWeight: 700 }}>{f.value}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{f.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Improvement Tips */}
          <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>💡 How to Improve Your Score</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {prediction.factors.topic_coverage < 80 && (
                <div style={{ padding: '0.75rem', borderRadius: '10px', background: 'rgba(245,158,11,0.1)', borderLeft: '3px solid #f59e0b' }}>
                  <strong>Increase Coverage:</strong> You've only assessed {prediction.factors.topic_coverage.toFixed(0)}% of topics. Take practice quizzes on remaining topics.
                </div>
              )}
              {prediction.factors.avg_mastery < 60 && (
                <div style={{ padding: '0.75rem', borderRadius: '10px', background: 'rgba(239,68,68,0.1)', borderLeft: '3px solid #ef4444' }}>
                  <strong>Boost Mastery:</strong> Average mastery is {prediction.factors.avg_mastery.toFixed(0)}%. Focus on weak topics with extra practice sessions.
                </div>
              )}
              {prediction.factors.study_streak < 5 && (
                <div style={{ padding: '0.75rem', borderRadius: '10px', background: 'rgba(99,102,241,0.1)', borderLeft: '3px solid #6366f1' }}>
                  <strong>Build Consistency:</strong> Maintain a daily study streak. Even 30 minutes daily helps retention.
                </div>
              )}
              {prediction.factors.assessments_completed < 5 && (
                <div style={{ padding: '0.75rem', borderRadius: '10px', background: 'rgba(139,92,246,0.1)', borderLeft: '3px solid #8b5cf6' }}>
                  <strong>Take More Assessments:</strong> With only {prediction.factors.assessments_completed} completed, take more quizzes for better prediction accuracy.
                </div>
              )}
              {prediction.predicted_score >= 80 && (
                <div style={{ padding: '0.75rem', borderRadius: '10px', background: 'rgba(34,197,94,0.1)', borderLeft: '3px solid #22c55e' }}>
                  <strong>Great Progress! 🎉</strong> You're on track for a strong score. Keep up the consistent effort!
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
