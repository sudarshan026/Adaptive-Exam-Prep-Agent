import { useState, useEffect } from 'react';
import api from '../services/api';

export default function ResourcesPage() {
  const [resources, setResources] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [discovered, setDiscovered] = useState(null);
  const [filter, setFilter] = useState('all');
  const [savedOnly, setSavedOnly] = useState(false);

  useEffect(() => {
    Promise.all([fetchResources(), fetchSubjects()]).finally(() => setLoading(false));
  }, []);

  const fetchResources = async () => {
    try {
      const res = await api.get('/syllabus/resources', { params: { saved_only: savedOnly } });
      setResources(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/syllabus/subjects');
      setSubjects(res.data);
      const allTopics = res.data.flatMap(s =>
        (s.topics || []).map(t => ({ ...t, subject_name: s.name }))
      );
      setTopics(allTopics);
    } catch (err) {
      console.error(err);
    }
  };

  const discoverResources = async () => {
    if (!selectedTopic) return;
    setDiscovering(true);
    setDiscovered(null);
    try {
      const topic = topics.find(t => t.name === selectedTopic);
      const res = await api.post('/analytics/discover-resources', null, {
        params: {
          topic_name: selectedTopic,
          subject_name: topic?.subject_name || selectedSubject || '',
          difficulty: topic?.difficulty || 'medium',
        }
      });
      setDiscovered(res.data);
      fetchResources(); // Refresh saved resources
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  const toggleSave = async (id) => {
    try {
      await api.put(`/syllabus/resources/${id}/save`);
      fetchResources();
    } catch (err) {
      console.error(err);
    }
  };

  const getTypeIcon = (type) => {
    const icons = { video: '🎬', article: '📄', book: '📖', notes: '📝', question_bank: '❓', course: '🎓' };
    return icons[type] || '📎';
  };

  const getTypeColor = (type) => {
    const colors = { video: '#ef4444', article: '#3b82f6', book: '#8b5cf6', notes: '#22c55e', question_bank: '#f59e0b', course: '#06b6d4' };
    return colors[type] || '#6366f1';
  };

  const filteredResources = resources.filter(r => {
    if (savedOnly && !r.is_saved) return false;
    if (filter !== 'all' && r.resource_type !== filter) return false;
    return true;
  });

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
          📚 <span className="gradient-text">Learning Resources</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Discover AI-curated resources for any topic in your syllabus
        </p>
      </div>

      {/* Discovery Panel */}
      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem', background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05))' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>🔍 Discover New Resources</h3>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>Topic</label>
            <select
              value={selectedTopic}
              onChange={e => setSelectedTopic(e.target.value)}
              style={{
                width: '100%', padding: '0.6rem 0.75rem', borderRadius: '10px',
                background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: '0.85rem',
              }}
            >
              <option value="">Select a topic...</option>
              {topics.map((t, i) => (
                <option key={i} value={t.name}>{t.subject_name}: {t.name}</option>
              ))}
            </select>
          </div>
          <button
            onClick={discoverResources}
            disabled={!selectedTopic || discovering}
            className="btn-primary"
            style={{ padding: '0.6rem 1.5rem', borderRadius: '10px', whiteSpace: 'nowrap' }}
          >
            {discovering ? '🔄 Discovering...' : '✨ Discover Resources'}
          </button>
        </div>

        {/* Discovered Results */}
        {discovered && (
          <div style={{ marginTop: '1rem' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              ✅ Found <strong>{discovered.resources.length}</strong> resources for <strong>{discovered.topic_name}</strong>
              {discovered.saved_count > 0 && ` • ${discovered.saved_count} saved to your library`}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
              {discovered.resources.map((r, i) => (
                <div key={i} style={{
                  padding: '1rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>{getTypeIcon(r.resource_type)}</span>
                    <span style={{
                      fontSize: '0.65rem', padding: '2px 8px', borderRadius: '8px', fontWeight: 600,
                      background: `${getTypeColor(r.resource_type)}22`,
                      color: getTypeColor(r.resource_type),
                      textTransform: 'capitalize',
                    }}>{r.resource_type}</span>
                  </div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.25rem' }}>{r.title}</h4>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>{r.description}</p>
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: '0.75rem', color: 'var(--primary-light)', textDecoration: 'none' }}>
                      Open Resource →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Saved Resources Library */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>📖 Your Resource Library ({filteredResources.length})</h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => { setSavedOnly(!savedOnly); }}
            className={savedOnly ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', borderRadius: '16px' }}
          >
            ⭐ Saved Only
          </button>
          {['all', 'video', 'article', 'book', 'notes', 'course'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={filter === f ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', borderRadius: '16px', textTransform: 'capitalize' }}
            >
              {f === 'all' ? 'All' : `${getTypeIcon(f)} ${f}`}
            </button>
          ))}
        </div>
      </div>

      {filteredResources.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <p style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📭</p>
          <p style={{ color: 'var(--text-muted)' }}>
            {savedOnly ? 'No saved resources yet. Use the discover feature above!' : 'No resources found. Discover some above!'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {filteredResources.map(r => (
            <div key={r.id} className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.5rem' }}>{getTypeIcon(r.resource_type)}</span>
                  <span style={{
                    fontSize: '0.65rem', padding: '2px 8px', borderRadius: '8px', fontWeight: 600,
                    background: `${getTypeColor(r.resource_type)}22`,
                    color: getTypeColor(r.resource_type),
                    textTransform: 'capitalize',
                  }}>{r.resource_type}</span>
                </div>
                <button
                  onClick={() => toggleSave(r.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem' }}
                  title={r.is_saved ? 'Unsave' : 'Save'}
                >
                  {r.is_saved ? '⭐' : '☆'}
                </button>
              </div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.25rem' }}>{r.title}</h4>
              {r.description && (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>{r.description}</p>
              )}
              {r.url && (
                <a href={r.url} target="_blank" rel="noopener noreferrer"
                  style={{ fontSize: '0.8rem', color: 'var(--primary-light)', textDecoration: 'none', fontWeight: 600 }}>
                  Open Resource →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
