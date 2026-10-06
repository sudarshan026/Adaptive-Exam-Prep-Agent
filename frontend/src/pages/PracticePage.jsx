import { useState, useEffect } from 'react';
import api from '../services/api';

export default function PracticePage() {
  const [mode, setMode] = useState('setup'); // setup, quiz, results
  const [subjects, setSubjects] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [config, setConfig] = useState({ topic_name: '', subject_name: '', difficulty: 'medium', num_questions: 5, time_limit_minutes: null });
  const [assessment, setAssessment] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [currentQ, setCurrentQ] = useState(0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    const interval = setInterval(() => setTimeLeft(prev => {
      if (prev <= 1) { clearInterval(interval); handleSubmit(); return 0; }
      return prev - 1;
    }), 1000);
    return () => clearInterval(interval);
  }, [timeLeft]);

  const fetchData = async () => {
    try {
      const [sRes, aRes] = await Promise.all([
        api.get('/syllabus/subjects'),
        api.get('/assessments/', { params: { status_filter: 'completed' } }),
      ]);
      setSubjects(sRes.data);
      setAssessments(aRes.data);
    } catch (err) { console.error(err); }
  };

  const startQuiz = async () => {
    if (!config.topic_name && !config.subject_name) {
      alert('Please enter a topic or subject name');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/assessments/create', config);
      setAssessment(res.data);
      const qRes = await api.get(`/assessments/${res.data.id}/questions`);
      setQuestions(qRes.data);
      setCurrentQ(0);
      setAnswers({});
      setMode('quiz');
      if (config.time_limit_minutes) {
        setTimeLeft(config.time_limit_minutes * 60);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create assessment');
    } finally { setLoading(false); }
  };

  const handleSubmit = async () => {
    if (!assessment) return;
    setLoading(true);
    try {
      const answerList = Object.entries(answers).map(([qid, ans]) => ({
        question_id: parseInt(qid), selected_answer: ans,
      }));
      const res = await api.post(`/assessments/${assessment.id}/submit`, {
        answers: answerList,
        time_taken_minutes: config.time_limit_minutes ? Math.ceil((config.time_limit_minutes * 60 - (timeLeft || 0)) / 60) : null,
      });
      setResults(res.data);
      setMode('results');
      setTimeLeft(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Submission failed');
    } finally { setLoading(false); }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // Setup Screen
  if (mode === 'setup') {
    const allTopics = subjects.flatMap(s => (s.topics || []).map(t => ({ ...t, subject_name: s.name })));
    return (
      <div className="page-container">
        <h1 className="page-title">✏️ Practice & Assessments</h1>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* New Quiz */}
          <div className="glass-card">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem' }}>🆕 Start New Quiz</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="form-label">Topic</label>
                {allTopics.length > 0 ? (
                  <select className="input-field" value={config.topic_name}
                    onChange={e => {
                      const t = allTopics.find(t => t.name === e.target.value);
                      setConfig({ ...config, topic_name: e.target.value, subject_name: t?.subject_name || '' });
                    }}>
                    <option value="">Select a topic</option>
                    {allTopics.map(t => <option key={t.id} value={t.name}>{t.subject_name} → {t.name}</option>)}
                  </select>
                ) : (
                  <input className="input-field" placeholder="e.g., Binary Trees"
                    value={config.topic_name} onChange={e => setConfig({ ...config, topic_name: e.target.value })} />
                )}
              </div>
              <div>
                <label className="form-label">Difficulty</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {['easy', 'medium', 'hard'].map(d => (
                    <button key={d} type="button" onClick={() => setConfig({ ...config, difficulty: d })}
                      style={{
                        flex: 1, padding: '0.6rem', borderRadius: '8px', border: '1px solid',
                        borderColor: config.difficulty === d ? 'var(--primary)' : 'var(--border)',
                        background: config.difficulty === d ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                        color: config.difficulty === d ? 'var(--primary-light)' : 'var(--text-secondary)',
                        cursor: 'pointer', fontWeight: 500, textTransform: 'capitalize',
                      }}>{d}</button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Questions</label>
                  <select className="input-field" value={config.num_questions}
                    onChange={e => setConfig({ ...config, num_questions: parseInt(e.target.value) })}>
                    {[3, 5, 10, 15, 20].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Time Limit</label>
                  <select className="input-field" value={config.time_limit_minutes || ''}
                    onChange={e => setConfig({ ...config, time_limit_minutes: e.target.value ? parseInt(e.target.value) : null })}>
                    <option value="">No limit</option>
                    {[5, 10, 15, 20, 30, 45, 60].map(n => <option key={n} value={n}>{n} min</option>)}
                  </select>
                </div>
              </div>
              <button className="btn-primary" onClick={startQuiz} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? '⏳ Generating...' : '🚀 Start Quiz'}
              </button>
            </div>
          </div>

          {/* History */}
          <div className="glass-card">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem' }}>📜 Assessment History</h2>
            {assessments.length === 0 ? (
              <div className="empty-state" style={{ padding: '1.5rem' }}>
                <p>No completed assessments yet</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '400px', overflow: 'auto' }}>
                {assessments.map(a => (
                  <div key={a.id} style={{
                    padding: '0.75rem', borderRadius: '8px', background: 'var(--bg-dark)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{a.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {a.total_questions} questions · {new Date(a.completed_at).toLocaleDateString()}
                      </div>
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

  // Quiz Screen
  if (mode === 'quiz') {
    const q = questions[currentQ];
    if (!q) return null;
    const progress = ((currentQ + 1) / questions.length) * 100;

    return (
      <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Top bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <span style={{ fontWeight: 600 }}>Question {currentQ + 1} of {questions.length}</span>
          {timeLeft !== null && (
            <span className={`badge ${timeLeft < 60 ? 'badge-danger' : 'badge-primary'}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
              ⏱️ {formatTime(timeLeft)}
            </span>
          )}
        </div>
        <div className="progress-bar" style={{ marginBottom: '1.5rem' }}>
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>

        {/* Question */}
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <span className={`badge ${q.difficulty === 'hard' ? 'badge-danger' : q.difficulty === 'easy' ? 'badge-success' : 'badge-warning'}`}>
            {q.difficulty}
          </span>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginTop: '0.75rem', lineHeight: 1.6 }}>
            {q.question_text}
          </h2>
        </div>

        {/* Options */}
        {q.options && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
            {q.options.map((opt, i) => (
              <button key={i} onClick={() => setAnswers({ ...answers, [q.id]: opt })}
                style={{
                  padding: '1rem 1.25rem', borderRadius: '12px', border: '2px solid',
                  borderColor: answers[q.id] === opt ? 'var(--primary)' : 'var(--border)',
                  background: answers[q.id] === opt ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card)',
                  color: 'var(--text-primary)', cursor: 'pointer', textAlign: 'left',
                  fontWeight: answers[q.id] === opt ? 600 : 400, fontSize: '0.95rem',
                  transition: 'all 0.2s ease',
                }}>
                {opt}
              </button>
            ))}
          </div>
        )}

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <button className="btn-secondary" disabled={currentQ === 0} onClick={() => setCurrentQ(currentQ - 1)}>
            ← Previous
          </button>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {currentQ < questions.length - 1 ? (
              <button className="btn-primary" onClick={() => setCurrentQ(currentQ + 1)}>Next →</button>
            ) : (
              <button className="btn-success" onClick={handleSubmit} disabled={loading}>
                {loading ? '⏳ Submitting...' : '📤 Submit'}
              </button>
            )}
          </div>
        </div>

        {/* Question dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.35rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
          {questions.map((_, i) => (
            <button key={i} onClick={() => setCurrentQ(i)} style={{
              width: '32px', height: '32px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              fontSize: '0.75rem', fontWeight: 600,
              background: i === currentQ ? 'var(--primary)' : answers[questions[i]?.id] ? 'var(--success)' : 'var(--bg-card)',
              color: 'white',
            }}>{i + 1}</button>
          ))}
        </div>
      </div>
    );
  }

  // Results Screen
  if (mode === 'results' && results) {
    return (
      <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="glass-card" style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>
            {results.assessment.accuracy >= 80 ? '🎉' : results.assessment.accuracy >= 50 ? '👍' : '💪'}
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            <span className="gradient-text">{results.assessment.accuracy?.toFixed(0)}%</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Score: {results.assessment.score}/{results.assessment.total_marks} · {results.assessment.total_questions} questions
          </p>
          {results.weak_topics_identified.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--danger)' }}>
                ⚠️ Weak topics: {results.weak_topics_identified.join(', ')}
              </span>
            </div>
          )}
        </div>

        {/* Topic Breakdown */}
        {results.topic_breakdown.length > 0 && (
          <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>📊 Topic Breakdown</h3>
            {results.topic_breakdown.map((tb, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                <span>{tb.topic_name}</span>
                <span className={`badge ${tb.accuracy >= 70 ? 'badge-success' : tb.accuracy >= 50 ? 'badge-warning' : 'badge-danger'}`}>
                  {tb.correct}/{tb.total} ({tb.accuracy}%)
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Questions Review */}
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>📝 Question Review</h3>
          {results.questions.map((q, i) => {
            const resp = results.responses.find(r => r.question_id === q.id);
            return (
              <div key={i} style={{
                padding: '1rem', marginBottom: '0.75rem', borderRadius: '10px',
                background: resp?.is_correct ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                border: '1px solid',
                borderColor: resp?.is_correct ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                  {resp?.is_correct ? '✅' : '❌'} Q{i + 1}: {q.question_text}
                </div>
                {resp && !resp.is_correct && (
                  <div style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                    <span style={{ color: 'var(--danger)' }}>Your answer: {resp.selected_answer}</span>
                  </div>
                )}
                <div style={{ fontSize: '0.85rem', color: 'var(--success)' }}>
                  Correct: {q.correct_answer}
                </div>
                {q.explanation && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontStyle: 'italic' }}>
                    💡 {q.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button className="btn-primary" onClick={() => { setMode('setup'); fetchData(); }}>
            📝 New Quiz
          </button>
          <button className="btn-secondary" onClick={async () => {
            try {
              await api.post('/analytics/adapt-plan');
              alert('Study plan adapted based on results!');
            } catch (err) { alert(err.response?.data?.detail || 'Adaptation failed'); }
          }}>
            🔄 Adapt Study Plan
          </button>
        </div>
      </div>
    );
  }

  return null;
}
