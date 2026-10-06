import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';

export default function TutorPage() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [topicName, setTopicName] = useState(searchParams.get('topic') || '');
  const [topicId, setTopicId] = useState(searchParams.get('topicId') || '');
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    if (topicName && messages.length === 0) {
      handleExplain(topicName);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/tutor/history', { params: { limit: 30 } });
      setMessages(res.data.map(m => ({ role: m.role, content: m.content, topic_name: m.topic_name })));
    } catch (err) { console.error(err); }
  };

  const handleExplain = async (topic) => {
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: `Explain: ${topic}` }]);
    try {
      const res = await api.post('/tutor/explain', {
        content: topic, topic_name: topic, topic_id: topicId ? parseInt(topicId) : null,
      });
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.data.content,
        is_demo_mode: res.data.is_demo_mode,
      }]);
      setSuggestions(res.data.suggested_questions || []);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally { setLoading(false); }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await api.post('/tutor/chat', {
        content: msg, topic_name: topicName, topic_id: topicId ? parseInt(topicId) : null,
      });
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.data.content,
        is_demo_mode: res.data.is_demo_mode,
      }]);
      setSuggestions(res.data.suggested_questions || []);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not get a response. Please try again.' }]);
    } finally { setLoading(false); }
  };

  const clearHistory = async () => {
    try {
      await api.delete('/tutor/history');
      setMessages([]);
      setSuggestions([]);
    } catch (err) { console.error(err); }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'var(--bg-card)',
      }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🤖 AI Tutor
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {topicName ? `Topic: ${topicName}` : 'Ask me anything about your syllabus'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input className="input-field" style={{ width: '200px', padding: '0.5rem 0.75rem' }}
            placeholder="Set topic context..."
            value={topicName} onChange={e => setTopicName(e.target.value)} />
          <button className="btn-secondary" style={{ padding: '0.5rem 0.75rem', fontSize: '0.8rem' }}
            onClick={clearHistory}>Clear Chat</button>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
            <h2 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Start a Conversation</h2>
            <p style={{ marginBottom: '1.5rem' }}>Ask me to explain any topic, or type a question below</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
              {['Explain Binary Search Trees', 'What is TCP/IP?', 'How does RAM work?', 'Explain Dijkstra\'s algorithm'].map((q, i) => (
                <button key={i} className="btn-secondary" style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                  onClick={() => { setInput(q); }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div className={`chat-bubble ${msg.role}`}>
              {msg.is_demo_mode && (
                <span className="badge badge-warning" style={{ marginBottom: '0.5rem', display: 'inline-flex' }}>Demo Mode</span>
              )}
              <div className="markdown-content" style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div className="chat-bubble assistant" style={{ display: 'flex', gap: '0.3rem', padding: '1rem 1.5rem' }}>
              <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
              <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div style={{ padding: '0.5rem 1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', borderTop: '1px solid var(--border)' }}>
          {suggestions.map((q, i) => (
            <button key={i} className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              onClick={() => { setInput(q); }}>
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '1rem 1.5rem', borderTop: '1px solid var(--border)', background: 'var(--bg-card)',
        display: 'flex', gap: '0.75rem',
      }}>
        <input className="input-field" placeholder="Ask a question or request an explanation..."
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading} style={{ flex: 1 }} />
        <button className="btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? '⏳' : '📤'} Send
        </button>
      </div>
    </div>
  );
}
