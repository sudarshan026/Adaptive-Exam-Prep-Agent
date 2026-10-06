import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/study-plan', label: 'Study Plan', icon: '📅' },
  { path: '/syllabus', label: 'Syllabus', icon: '📚' },
  { path: '/tutor', label: 'AI Tutor', icon: '🤖' },
  { path: '/practice', label: 'Practice', icon: '✏️' },
  { path: '/analytics', label: 'Analytics', icon: '📈' },
  { path: '/coaching', label: 'Coaching', icon: '🏆' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarOpen ? '250px' : '70px',
        background: 'var(--bg-card)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: 100,
        overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{
          padding: '1.25rem',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          cursor: 'pointer',
        }} onClick={() => setSidebarOpen(!sidebarOpen)}>
          <span style={{ fontSize: '1.5rem' }}>🎓</span>
          {sidebarOpen && (
            <span style={{ fontWeight: 700, fontSize: '1rem', whiteSpace: 'nowrap' }}>
              ExamPrep <span className="gradient-text">AI</span>
            </span>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem',
                borderRadius: '10px',
                textDecoration: 'none',
                color: isActive ? 'var(--primary-light)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.9rem',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              })}
            >
              <span style={{ fontSize: '1.15rem', minWidth: '24px', textAlign: 'center' }}>{item.icon}</span>
              {sidebarOpen && item.label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div style={{
          padding: '1rem',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 700, fontSize: '0.85rem', flexShrink: 0,
          }}>
            {user?.full_name?.[0]?.toUpperCase() || 'U'}
          </div>
          {sidebarOpen && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.full_name}
              </div>
              <button onClick={handleLogout} style={{
                background: 'none', border: 'none', color: 'var(--text-muted)',
                fontSize: '0.75rem', cursor: 'pointer', padding: 0,
              }}>
                Sign out
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        marginLeft: sidebarOpen ? '250px' : '70px',
        transition: 'margin-left 0.3s ease',
        minHeight: '100vh',
      }}>
        <Outlet />
      </main>
    </div>
  );
}
