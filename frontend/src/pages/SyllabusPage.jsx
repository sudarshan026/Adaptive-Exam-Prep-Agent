import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function SyllabusPage() {
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [showAddTopic, setShowAddTopic] = useState(null);
  const [newSubject, setNewSubject] = useState({ name: '', description: '' });
  const [newTopic, setNewTopic] = useState({ name: '', difficulty: 'medium', estimated_hours: 2 });

  useEffect(() => { fetchSubjects(); }, []);

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/syllabus/subjects');
      setSubjects(res.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/syllabus/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.parsed_structure?.subjects) {
        for (const s of res.data.parsed_structure.subjects) {
          const sRes = await api.post('/syllabus/subjects', { name: s.name, description: '' });
          for (const t of (s.topics || [])) {
            await api.post('/syllabus/topics', {
              subject_id: sRes.data.id, name: t.name,
              difficulty: t.difficulty || 'medium',
              estimated_hours: t.estimated_hours || 2,
            });
          }
        }
        fetchSubjects();
      }
      alert(res.data.status === 'parsed' ? 'Syllabus parsed! Review subjects below.' : 'PDF uploaded. Add subjects manually.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally { setUploading(false); }
  };

  const addSubject = async () => {
    if (!newSubject.name) return;
    try {
      await api.post('/syllabus/subjects', newSubject);
      setNewSubject({ name: '', description: '' });
      setShowAddSubject(false);
      fetchSubjects();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const addTopic = async (subjectId) => {
    if (!newTopic.name) return;
    try {
      await api.post('/syllabus/topics', { subject_id: subjectId, ...newTopic });
      setNewTopic({ name: '', difficulty: 'medium', estimated_hours: 2 });
      setShowAddTopic(null);
      fetchSubjects();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const deleteSubject = async (id) => {
    if (!confirm('Delete this subject and all its topics?')) return;
    try { await api.delete(`/syllabus/subjects/${id}`); fetchSubjects(); }
    catch (err) { alert('Failed to delete'); }
  };

  const deleteTopic = async (id) => {
    try { await api.delete(`/syllabus/topics/${id}`); fetchSubjects(); }
    catch (err) { alert('Failed to delete'); }
  };

  const COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ec4899', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'];

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}><div className="spinner"></div></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: '0.25rem' }}>📚 Syllabus Management</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Upload a PDF or manually manage your subjects and topics</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <label className="btn-secondary" style={{ cursor: 'pointer' }}>
            {uploading ? '⏳ Uploading...' : '📄 Upload PDF'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} disabled={uploading} />
          </label>
          <button className="btn-primary" onClick={() => setShowAddSubject(true)}>+ Add Subject</button>
        </div>
      </div>

      {/* Add Subject Modal */}
      {showAddSubject && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>New Subject</h3>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="form-label">Subject Name</label>
              <input className="input-field" placeholder="e.g., Computer Networks"
                value={newSubject.name} onChange={e => setNewSubject({ ...newSubject, name: e.target.value })} />
            </div>
            <button className="btn-primary" onClick={addSubject}>Add</button>
            <button className="btn-secondary" onClick={() => setShowAddSubject(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Subjects */}
      {subjects.length === 0 ? (
        <div className="glass-card empty-state">
          <div className="empty-icon">📚</div>
          <h3>No Subjects Yet</h3>
          <p>Upload a syllabus PDF or add subjects manually to get started</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {subjects.map((subject, si) => (
            <div key={subject.id} className="glass-card" style={{ borderLeft: `4px solid ${COLORS[si % COLORS.length]}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{subject.name}</h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {subject.topics?.length || 0} topics · {subject.topics?.filter(t => t.is_completed).length || 0} completed
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn-secondary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                    onClick={() => setShowAddTopic(showAddTopic === subject.id ? null : subject.id)}>+ Topic</button>
                  <button style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.85rem' }}
                    onClick={() => deleteSubject(subject.id)}>🗑️</button>
                </div>
              </div>

              {/* Add Topic */}
              {showAddTopic === subject.id && (
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: '200px' }}>
                    <label className="form-label">Topic Name</label>
                    <input className="input-field" placeholder="e.g., TCP/IP Protocol"
                      value={newTopic.name} onChange={e => setNewTopic({ ...newTopic, name: e.target.value })} />
                  </div>
                  <div style={{ width: '120px' }}>
                    <label className="form-label">Difficulty</label>
                    <select className="input-field" value={newTopic.difficulty}
                      onChange={e => setNewTopic({ ...newTopic, difficulty: e.target.value })}>
                      <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
                    </select>
                  </div>
                  <div style={{ width: '100px' }}>
                    <label className="form-label">Hours</label>
                    <input type="number" className="input-field" min="0.5" step="0.5"
                      value={newTopic.estimated_hours} onChange={e => setNewTopic({ ...newTopic, estimated_hours: parseFloat(e.target.value) })} />
                  </div>
                  <button className="btn-primary" style={{ padding: '0.6rem 1rem' }} onClick={() => addTopic(subject.id)}>Add</button>
                </div>
              )}

              {/* Topics */}
              {subject.topics && subject.topics.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {subject.topics.map(topic => (
                    <div key={topic.id} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.6rem 0.75rem', borderRadius: '8px', background: 'var(--bg-dark)',
                      opacity: topic.is_completed ? 0.6 : 1,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '0.85rem' }}>{topic.is_completed ? '✅' : '📖'}</span>
                        <div>
                          <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{topic.name}</span>
                          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.15rem' }}>
                            <span className={`badge ${topic.difficulty === 'hard' ? 'badge-danger' : topic.difficulty === 'easy' ? 'badge-success' : 'badge-warning'}`}>
                              {topic.difficulty}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{topic.estimated_hours}h</span>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.85rem' }}
                          onClick={() => navigate(`/tutor?topic=${topic.name}&topicId=${topic.id}`)}>🤖</button>
                        <button style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem' }}
                          onClick={() => deleteTopic(topic.id)}>×</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
