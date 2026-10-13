import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [filter, setFilter] = useState('all');
  const canvasRef = useRef(null);
  const [positions, setPositions] = useState({});
  const [dragging, setDragging] = useState(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => { fetchGraph(); }, []);

  const fetchGraph = async () => {
    try {
      const res = await api.get('/analytics/knowledge-graph');
      setGraphData(res.data);
      if (res.data.nodes.length > 0) {
        initPositions(res.data);
      }
    } catch (err) {
      setError('Failed to load knowledge graph');
    } finally {
      setLoading(false);
    }
  };

  const initPositions = (data) => {
    const pos = {};
    const groups = {};
    data.nodes.forEach(n => {
      if (!groups[n.subject_id]) groups[n.subject_id] = [];
      groups[n.subject_id].push(n.id);
    });

    const groupKeys = Object.keys(groups);
    const centerX = 450;
    const centerY = 350;
    const radiusX = 320;
    const radiusY = 250;

    groupKeys.forEach((gk, gi) => {
      const angle = (gi / groupKeys.length) * 2 * Math.PI - Math.PI / 2;
      const gx = centerX + radiusX * Math.cos(angle);
      const gy = centerY + radiusY * Math.sin(angle);
      const members = groups[gk];
      members.forEach((nodeId, ni) => {
        const subAngle = (ni / members.length) * 2 * Math.PI;
        const subR = 50 + members.length * 15;
        pos[nodeId] = {
          x: gx + subR * Math.cos(subAngle),
          y: gy + subR * Math.sin(subAngle),
        };
      });
    });
    setPositions(pos);
  };

  useEffect(() => {
    if (!graphData || !canvasRef.current || Object.keys(positions).length === 0) return;
    drawGraph();
  }, [graphData, positions, selectedNode, filter]);

  const drawGraph = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = 900 * dpr;
    canvas.height = 700 * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, 900, 700);

    // Background
    ctx.fillStyle = '#0f0f23';
    ctx.fillRect(0, 0, 900, 700);

    const nodes = filteredNodes();
    const nodeIds = new Set(nodes.map(n => n.id));

    // Draw edges
    (graphData.edges || []).forEach(edge => {
      if (!nodeIds.has(edge.from) || !nodeIds.has(edge.to)) return;
      const from = positions[edge.from];
      const to = positions[edge.to];
      if (!from || !to) return;

      ctx.beginPath();
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.35)';
      ctx.lineWidth = 1.5;
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();

      // Arrow
      const angle = Math.atan2(to.y - from.y, to.x - from.x);
      const arrowLen = 10;
      const ax = to.x - 22 * Math.cos(angle);
      const ay = to.y - 22 * Math.sin(angle);
      ctx.beginPath();
      ctx.fillStyle = 'rgba(99, 102, 241, 0.6)';
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - arrowLen * Math.cos(angle - 0.4), ay - arrowLen * Math.sin(angle - 0.4));
      ctx.lineTo(ax - arrowLen * Math.cos(angle + 0.4), ay - arrowLen * Math.sin(angle + 0.4));
      ctx.fill();
    });

    // Draw nodes
    nodes.forEach(node => {
      const p = positions[node.id];
      if (!p) return;

      const radius = 20;
      const mastery = node.mastery_score;
      const isSelected = selectedNode?.id === node.id;

      // Glow for selected
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, radius + 8, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';
        ctx.fill();
      }

      // Node circle with mastery-based color
      const hue = mastery > 70 ? 142 : mastery > 40 ? 45 : 0;
      const saturation = 70;
      const lightness = 50;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#fff' : 'rgba(255,255,255,0.2)';
      ctx.lineWidth = isSelected ? 2.5 : 1;
      ctx.stroke();

      // Mastery percentage inside circle
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${mastery.toFixed(0)}%`, p.x, p.y);

      // Label below
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.font = '10px Inter, sans-serif';
      const label = node.label.length > 18 ? node.label.substring(0, 16) + '…' : node.label;
      ctx.fillText(label, p.x, p.y + radius + 14);
    });
  };

  const filteredNodes = () => {
    if (!graphData) return [];
    if (filter === 'all') return graphData.nodes;
    if (filter === 'weak') return graphData.nodes.filter(n => n.mastery_score < 50);
    if (filter === 'strong') return graphData.nodes.filter(n => n.mastery_score >= 70);
    return graphData.nodes.filter(n => String(n.subject_id) === filter);
  };

  const handleCanvasClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const nodes = filteredNodes();
    for (const node of nodes) {
      const p = positions[node.id];
      if (!p) continue;
      const dist = Math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2);
      if (dist < 22) {
        setSelectedNode(node);
        return;
      }
    }
    setSelectedNode(null);
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const nodes = filteredNodes();
    for (const node of nodes) {
      const p = positions[node.id];
      if (!p) continue;
      const dist = Math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2);
      if (dist < 22) {
        setDragging(node.id);
        setOffset({ x: x - p.x, y: y - p.y });
        return;
      }
    }
  };

  const handleMouseMove = (e) => {
    if (!dragging) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setPositions(prev => ({
      ...prev,
      [dragging]: { x: x - offset.x, y: y - offset.y },
    }));
  };

  const handleMouseUp = () => setDragging(null);

  const getMasteryColor = (score) => {
    if (score >= 70) return '#22c55e';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const getDifficultyBadge = (d) => {
    const colors = { easy: '#22c55e', medium: '#f59e0b', hard: '#ef4444' };
    return { background: colors[d] || '#6366f1', color: '#fff', padding: '2px 8px', borderRadius: '8px', fontSize: '0.7rem', fontWeight: 600 };
  };

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;
  if (error) return <div className="page-container"><div className="glass-card" style={{ padding: '2rem', color: 'var(--danger)' }}>{error}</div></div>;

  return (
    <div className="page-container" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
          🔗 <span className="gradient-text">Knowledge Graph</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Visualize topic dependencies and mastery across your syllabus
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {['all', 'weak', 'strong'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={filter === f ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', borderRadius: '20px', textTransform: 'capitalize' }}
          >
            {f === 'all' ? '🌐 All Topics' : f === 'weak' ? '🔴 Weak (<50%)' : '🟢 Strong (≥70%)'}
          </button>
        ))}
        {graphData?.groups?.map(g => (
          <button
            key={g.id}
            onClick={() => setFilter(String(g.id))}
            className={filter === String(g.id) ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', borderRadius: '20px' }}
          >
            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: g.color, marginRight: 6 }} />
            {g.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 320px' : '1fr', gap: '1rem' }}>
        {/* Canvas */}
        <div className="glass-card" style={{ padding: '0.5rem', overflow: 'hidden' }}>
          {graphData?.nodes?.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
              <p>No topics found. Add subjects and topics to your syllabus first.</p>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              width={900}
              height={700}
              style={{ width: '100%', height: 'auto', cursor: dragging ? 'grabbing' : 'grab', borderRadius: '12px' }}
              onClick={handleCanvasClick}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            />
          )}

          {/* Legend */}
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', padding: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#22c55e', marginRight: 4 }} />
              High Mastery (≥70%)
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#f59e0b', marginRight: 4 }} />
              Medium (40-70%)
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#ef4444', marginRight: 4 }} />
              Weak (&lt;40%)
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              → Dependency Arrow
            </span>
          </div>
        </div>

        {/* Selected Node Panel */}
        {selectedNode && (
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>{selectedNode.label}</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Subject</span>
                <p style={{ fontWeight: 600 }}>{selectedNode.subject}</p>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Mastery</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                  <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.1)' }}>
                    <div style={{ width: `${selectedNode.mastery_score}%`, height: '100%', borderRadius: 4, background: getMasteryColor(selectedNode.mastery_score), transition: 'width 0.5s ease' }} />
                  </div>
                  <span style={{ fontWeight: 700, color: getMasteryColor(selectedNode.mastery_score) }}>{selectedNode.mastery_score.toFixed(0)}%</span>
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Difficulty</span>
                <p><span style={getDifficultyBadge(selectedNode.difficulty)}>{selectedNode.difficulty}</span></p>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Confidence</span>
                <p style={{ fontWeight: 600, textTransform: 'capitalize' }}>{selectedNode.confidence}</p>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status</span>
                <p style={{ fontWeight: 600 }}>{selectedNode.is_completed ? '✅ Completed' : '📖 In Progress'}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--primary-light)' }}>{graphData?.total_topics || 0}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Topics</div>
        </div>
        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent)' }}>{graphData?.total_edges || 0}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Dependencies</div>
        </div>
        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#22c55e' }}>{graphData?.groups?.length || 0}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Subject Groups</div>
        </div>
        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ef4444' }}>{graphData?.nodes?.filter(n => n.mastery_score < 50).length || 0}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Weak Topics</div>
        </div>
      </div>
    </div>
  );
}
