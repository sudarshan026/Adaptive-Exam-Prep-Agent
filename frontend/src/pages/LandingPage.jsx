import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const features = [
    { icon: '🧠', title: 'AI-Powered Tutoring', desc: 'Get personalized explanations and concept breakdowns from an AI tutor that adapts to your learning style.' },
    { icon: '📊', title: 'Adaptive Study Plans', desc: 'Smart scheduling that prioritizes weak areas and adjusts based on your performance in assessments.' },
    { icon: '📝', title: 'Practice & Assessments', desc: 'AI-generated questions at multiple difficulty levels with instant scoring and detailed explanations.' },
    { icon: '🎯', title: 'Weakness Detection', desc: 'Automatic identification of weak topics with evidence-based analysis and targeted revision plans.' },
    { icon: '📈', title: 'Performance Analytics', desc: 'Track mastery, accuracy trends, study streaks, and estimated exam performance over time.' },
    { icon: '🔄', title: 'Continuous Adaptation', desc: 'Learn → Practice → Test → Analyze → Adapt → Improve. Your study plan evolves with you.' },
  ];

  return (
    <div style={{ minHeight: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <header style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '1.25rem 2rem', borderBottom: '1px solid var(--border)',
        background: 'rgba(15, 23, 42, 0.95)', backdropFilter: 'blur(10px)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.75rem' }}>🎓</span>
          <span style={{ fontWeight: 700, fontSize: '1.25rem' }}>
            ExamPrep <span className="gradient-text">AI</span>
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {user ? (
            <button className="btn-primary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
          ) : (
            <>
              <button className="btn-secondary" onClick={() => navigate('/login')}>Login</button>
              <button className="btn-primary" onClick={() => navigate('/register')}>Get Started Free</button>
            </>
          )}
        </div>
      </header>

      {/* Hero */}
      <section style={{
        textAlign: 'center', padding: '6rem 2rem 4rem',
        background: 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15) 0%, transparent 60%)',
      }}>
        <div className="animate-slide-up">
          <span className="badge badge-primary" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
            ✨ AI-Powered Adaptive Learning
          </span>
          <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 800, lineHeight: 1.2, marginBottom: '1.5rem', maxWidth: '800px', margin: '0 auto 1.5rem' }}>
            Your Personal <span className="gradient-text">AI Exam Coach</span> That Adapts to You
          </h1>
          <p style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 2.5rem', lineHeight: 1.7 }}>
            Upload your syllabus, get a personalized study plan, learn with AI tutoring,
            practice with adaptive assessments, and watch your weak areas transform into strengths.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary pulse-glow" style={{ padding: '1rem 2.5rem', fontSize: '1.05rem' }}
              onClick={() => navigate(user ? '/dashboard' : '/register')}>
              🚀 Start Preparing Now
            </button>
            <button className="btn-secondary" style={{ padding: '1rem 2rem' }}
              onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
              Learn More ↓
            </button>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section style={{
        display: 'flex', justifyContent: 'center', gap: '3rem', padding: '2rem',
        borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)',
        flexWrap: 'wrap',
      }}>
        {[
          { value: '10', label: 'AI Agents' },
          { value: '∞', label: 'Practice Questions' },
          { value: '24/7', label: 'AI Tutor' },
          { value: '100%', label: 'Adaptive' },
        ].map((s, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }} className="gradient-text">{s.value}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </section>

      {/* Features */}
      <section id="features" style={{ padding: '5rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: '2rem', fontWeight: 700, marginBottom: '0.75rem' }}>
          Everything You Need to <span className="gradient-text">Ace Your Exam</span>
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem' }}>
          Powered by 10 specialized AI agents working together to optimize your study journey.
        </p>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem',
        }}>
          {features.map((f, i) => (
            <div key={i} className="glass-card animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>{f.icon}</div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>{f.title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section style={{
        padding: '5rem 2rem',
        background: 'linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.05))',
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: '2rem', fontWeight: 700, marginBottom: '3rem' }}>
            How It <span className="gradient-text">Works</span>
          </h2>
          {[
            { step: '01', title: 'Set Up Your Profile', desc: 'Enter your exam details, available study time, and subjects you find easy or challenging.' },
            { step: '02', title: 'Upload Your Syllabus', desc: 'Upload a PDF or manually add subjects and topics. AI extracts and structures the content.' },
            { step: '03', title: 'Get Your Study Plan', desc: 'Receive a personalized, priority-weighted study schedule that fits your daily availability.' },
            { step: '04', title: 'Learn & Practice', desc: 'Study with AI explanations, then test yourself with generated practice questions.' },
            { step: '05', title: 'Assess & Adapt', desc: 'Take assessments, see weak areas identified, and watch your plan automatically adjust.' },
          ].map((item, i) => (
            <div key={i} style={{
              display: 'flex', gap: '1.5rem', alignItems: 'flex-start',
              marginBottom: '2rem', padding: '1.5rem',
              borderLeft: '3px solid var(--primary)',
              background: 'rgba(99, 102, 241, 0.05)',
              borderRadius: '0 12px 12px 0',
            }}>
              <span className="gradient-text" style={{ fontSize: '2rem', fontWeight: 800, flexShrink: 0 }}>{item.step}</span>
              <div>
                <h3 style={{ fontWeight: 700, marginBottom: '0.25rem' }}>{item.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{
        padding: '5rem 2rem', textAlign: 'center',
        background: 'radial-gradient(ellipse at bottom, rgba(99, 102, 241, 0.15) 0%, transparent 60%)',
      }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
          Ready to Transform Your <span className="gradient-text">Exam Prep</span>?
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
          Join now and let AI guide you to exam success.
        </p>
        <button className="btn-primary pulse-glow" style={{ padding: '1rem 3rem', fontSize: '1.05rem' }}
          onClick={() => navigate(user ? '/dashboard' : '/register')}>
          🎓 Get Started Free
        </button>
      </section>

      {/* Footer */}
      <footer style={{
        textAlign: 'center', padding: '2rem',
        borderTop: '1px solid var(--border)',
        color: 'var(--text-muted)', fontSize: '0.85rem',
      }}>
        PS-03: Adaptive Exam Prep Agent — Built with AI-powered adaptive learning
      </footer>
    </div>
  );
}
