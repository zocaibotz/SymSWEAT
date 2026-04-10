import React, { useState, useEffect } from 'react';

// Style tokens from UX spec
const styles = {
  colors: {
    primary: '#3B82F6',
    primaryHover: '#2563EB',
    secondary: '#64748B',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    background: '#F8FAFC',
    surface: '#FFFFFF',
    textMain: '#1E293B',
    textMuted: '#64748B',
  },
  typography: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    headingWeight: '700',
    bodyWeight: '400',
    baseSize: '16px',
  },
  spacing: {
    containerPadding: '2rem',
    cardPadding: '1.5rem',
    elementGap: '1rem',
  },
  visualEffects: {
    borderRadius: '8px',
    shadowCard: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
    transition: 'all 0.2s ease-in-out',
  },
};

// Icons as simple SVG components
const Icons = {
  Menu: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 5h14M3 10h14M3 15h14" />
    </svg>
  ),
  X: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M5 5l10 10M15 5L5 15" />
    </svg>
  ),
  Plus: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 4v12M4 10h12" />
    </svg>
  ),
  Check: () => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 8l4 4 6-8" />
    </svg>
  ),
  Trash: () => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5M3 4l1 10h8l1-10" />
    </svg>
  ),
  Edit: () => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" />
    </svg>
  ),
  Download: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 3v10M6 9l4 4 4-4M3 14v3h14v-3" />
    </svg>
  ),
  Logout: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M7 17H4a2 2 0 01-2-2V5a2 2 0 012-2h3M13 14l4-4-4-4M17 10H6" />
    </svg>
  ),
  Dashboard: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="6" height="6" rx="1" />
      <rect x="11" y="3" width="6" height="6" rx="1" />
      <rect x="3" y="11" width="6" height="6" rx="1" />
      <rect x="11" y="11" width="6" height="6" rx="1" />
    </svg>
  ),
  Task: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 5h14M3 10h14M3 15h10" />
    </svg>
  ),
  Alert: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 3L2 17h16L10 3zM10 8v4M10 14v1" />
    </svg>
  ),
  Report: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 2h12a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2zM8 6h8M8 10h8M8 14h4" />
    </svg>
  ),
};

// Initial data for demo
const initialTasks = [
  { id: 1, title: 'Deploy v2.1 to production', description: 'Push the latest release with bug fixes', status: 'in_progress', dueDate: '2025-01-15' },
  { id: 2, title: 'Review pull request #142', description: 'Security audit for auth module', status: 'todo', dueDate: '2025-01-16' },
  { id: 3, title: 'Update API documentation', description: 'Add new endpoints for v2.1', status: 'done', dueDate: '2025-01-10' },
  { id: 4, title: 'Set up monitoring alerts', description: 'Configure PagerDuty for critical services', status: 'todo', dueDate: '2025-01-18' },
];

const initialIncidents = [
  { id: 1, title: 'Database connection timeout', severity: 'critical', status: 'resolved', resolution: 'Increased connection pool size, added read replicas', createdAt: '2025-01-10' },
  { id: 2, title: 'API rate limiting triggered', severity: 'high', status: 'resolved', resolution: 'Adjusted rate limits for batch jobs', createdAt: '2025-01-12' },
  { id: 3, title: 'Memory leak in worker process', severity: 'medium', status: 'open', resolution: '', createdAt: '2025-01-14' },
];

// LocalStorage helpers
const getStoredData = (key, initial) => {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initial;
  } catch {
    return initial;
  }
};

const setStoredData = (key, data) => {
  localStorage.setItem(key, JSON.stringify(data));
};

// Authentication Screen Component
const AuthScreen = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    // Simulate auth - in production this would call an API
    onLogin({ email, name: email.split('@')[0] });
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: styles.colors.background,
      fontFamily: styles.typography.fontFamily,
      padding: styles.spacing.containerPadding,
    }}>
      <div style={{
        background: styles.colors.surface,
        padding: '2.5rem',
        borderRadius: styles.visualEffects.borderRadius,
        boxShadow: styles.visualEffects.shadowCard,
        width: '100%',
        maxWidth: '400px',
      }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: styles.typography.headingWeight,
          color: styles.colors.textMain,
          marginBottom: '0.5rem',
          textAlign: 'center',
        }}>
          {isRegister ? 'Create Account' : 'Welcome Back'}
        </h1>
        <p style={{
          color: styles.colors.textMuted,
          textAlign: 'center',
          marginBottom: '2rem',
        }}>
          {isRegister ? 'Start tracking your operations' : 'Sign in to your dashboard'}
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.5rem',
              color: styles.colors.textMain,
              fontWeight: 500,
            }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                outline: 'none',
                transition: styles.visualEffects.transition,
                boxSizing: 'border-box',
              }}
              onFocus={(e) => e.target.style.borderColor = styles.colors.primary}
              onBlur={(e) => e.target.style.borderColor = '#E2E8F0'}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.5rem',
              color: styles.colors.textMain,
              fontWeight: 500,
            }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                outline: 'none',
                transition: styles.visualEffects.transition,
                boxSizing: 'border-box',
              }}
              onFocus={(e) => e.target.style.borderColor = styles.colors.primary}
              onBlur={(e) => e.target.style.borderColor = '#E2E8F0'}
            />
          </div>

          {error && (
            <div style={{
              color: styles.colors.danger,
              marginBottom: '1rem',
              fontSize: '0.875rem',
            }}>{error}</div>
          )}

          <button
            type="submit"
            style={{
              width: '100%',
              padding: '0.875rem',
              background: styles.colors.primary,
              color: '#FFF',
              border: 'none',
              borderRadius: styles.visualEffects.borderRadius,
              fontSize: styles.typography.baseSize,
              fontWeight: 600,
              fontFamily: styles.typography.fontFamily,
              cursor: 'pointer',
              transition: styles.visualEffects.transition,
            }}
            onMouseOver={(e) => e.target.style.background = styles.colors.primaryHover}
            onMouseOut={(e) => e.target.style.background = styles.colors.primary}
          >
            {isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <p style={{
          marginTop: '1.5rem',
          textAlign: 'center',
          color: styles.colors.textMuted,
        }}>
          {isRegister ? 'Already have an account?' : "Don't have an account?" }{' '}
          <button
            onClick={() => setIsRegister(!isRegister)}
            style={{
              background: 'none',
              border: 'none',
              color: styles.colors.primary,
              cursor: 'pointer',
              fontWeight: 500,
              fontFamily: styles.typography.fontFamily,
            }}
          >
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </p>
      </div>
    </div>
  );
};

// Sidebar Navigation Component
const Sidebar = ({ currentScreen, setScreen, onLogout, isOpen, setIsOpen }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.Dashboard },
    { id: 'tasks', label: 'Tasks', icon: Icons.Task },
    { id: 'incidents', label: 'Incidents', icon: Icons.Alert },
    { id: 'digest', label: 'Weekly Digest', icon: Icons.Report },
  ];

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'none',
          position: 'fixed',
          top: '1rem',
          left: '1rem',
          zIndex: 50,
          padding: '0.5rem',
          background: styles.colors.surface,
          border: '1px solid #E2E8F0',
          borderRadius: styles.visualEffects.borderRadius,
          cursor: 'pointer',
        }}
        className="mobile-menu-btn"
      >
        {isOpen ? <Icons.X /> : <Icons.Menu />}
      </button>

      <aside style={{
        width: '260px',
        background: styles.colors.surface,
        borderRight: '1px solid #E2E8F0',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 40,
        fontFamily: styles.typography.fontFamily,
      }}>
        <div style={{
          padding: styles.spacing.containerPadding,
          borderBottom: '1px solid #E2E8F0',
        }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: styles.typography.headingWeight,
            color: styles.colors.primary,
          }}>OpsTracker</h2>
          <p style={{
            fontSize: '0.875rem',
            color: styles.colors.textMuted,
            marginTop: '0.25rem',
          }}>Operations Dashboard</p>
        </div>

        <nav style={{ flex: 1, padding: '1rem' }}>
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setScreen(item.id);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                marginBottom: '0.25rem',
                background: currentScreen === item.id ? `${styles.colors.primary}10` : 'transparent',
                color: currentScreen === item.id ? styles.colors.primary : styles.colors.textMuted,
                border: 'none',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontWeight: currentScreen === item.id ? 600 : 400,
                cursor: 'pointer',
                transition: styles.visualEffects.transition,
                textAlign: 'left',
              }}
            >
              <item.icon />
              {item.label}
            </button>
          ))}
        </nav>

        <div style={{
          padding: '1rem',
          borderTop: '1px solid #E2E8F0',
        }}>
          <button
            onClick={onLogout}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              background: 'transparent',
              color: styles.colors.textMuted,
              border: 'none',
              borderRadius: styles.visualEffects.borderRadius,
              fontSize: styles.typography.baseSize,
              cursor: 'pointer',
              transition: styles.visualEffects.transition,
            }}
          >
            <Icons.Logout />
            Sign Out
          </button>
        </div>
      </aside>

      <style>{`
        @media (max-width: 768px) {
          .mobile-menu-btn { display: block !important; }
          aside { transform: translateX(${isOpen ? '0' : '-100%'}); }
        }
      `}</style>
    </>
  );
};

// Dashboard Screen Component
const DashboardScreen = ({ tasks, incidents, onNewTask, onNewIncident }) => {
  const openTasks = tasks.filter(t => t.status !== 'done').length;
  const criticalIncidents = incidents.filter(i => i.severity === 'critical' && i.status !== 'resolved').length;
  const completedTasks = tasks.filter(t => t.status === 'done').length;
  const openIncidents = incidents.filter(i => i.status !== 'resolved').length;

  // Calculate severity distribution
  const severityCounts = {
    critical: incidents.filter(i => i.severity === 'critical').length,
    high: incidents.filter(i => i.severity === 'high').length,
    medium: incidents.filter(i => i.severity === 'medium').length,
    low: incidents.filter(i => i.severity === 'low').length,
  };

  const totalIncidents = incidents.length || 1;

  return (
    <div style={{
      padding: styles.spacing.containerPadding,
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      <h1 style={{
        fontSize: '1.75rem',
        fontWeight: styles.typography.headingWeight,
        color: styles.colors.textMain,
        marginBottom: '1.5rem',
      }}>Operations Dashboard</h1>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: styles.spacing.elementGap,
        marginBottom: '2rem',
      }}>
        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <p style={{ color: styles.colors.textMuted, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Open Tasks</p>
          <p style={{ fontSize: '2rem', fontWeight: styles.typography.headingWeight, color: styles.colors.textMain }}>{openTasks}</p>
        </div>

        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <p style={{ color: styles.colors.textMuted, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Critical Incidents</p>
          <p style={{ fontSize: '2rem', fontWeight: styles.typography.headingWeight, color: criticalIncidents > 0 ? styles.colors.danger : styles.colors.success }}>{criticalIncidents}</p>
        </div>

        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <p style={{ color: styles.colors.textMuted, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Completed Tasks</p>
          <p style={{ fontSize: '2rem', fontWeight: styles.typography.headingWeight, color: styles.colors.success }}>{completedTasks}</p>
        </div>

        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <p style={{ color: styles.colors.textMuted, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Open Incidents</p>
          <p style={{ fontSize: '2rem', fontWeight: styles.typography.headingWeight, color: openIncidents > 0 ? styles.colors.warning : styles.colors.textMain }}>{openIncidents}</p>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: styles.spacing.elementGap,
        marginBottom: '2rem',
      }}>
        {/* Severity Distribution Chart */}
        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: styles.colors.textMain, marginBottom: '1rem' }}>Incidents by Severity</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            {/* Simple bar chart */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem', height: '120px' }}>
              {Object.entries(severityCounts).map(([severity, count]) => {
                const height = (count / totalIncidents) * 100 || 10;
                const colors = {
                  critical: styles.colors.danger,
                  high: styles.colors.warning,
                  medium: '#F59E0B80',
                  low: styles.colors.success,
                };
                return (
                  <div key={severity} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <div style={{
                      width: '40px',
                      height: `${height}px`,
                      background: colors[severity],
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.3s ease',
                    }} />
                    <span style={{ fontSize: '0.75rem', color: styles.colors.textMuted, textTransform: 'uppercase' }}>{count}</span>
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {Object.entries({ critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' }).map(([key, label]) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                  <div style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '2px',
                    background: key === 'critical' ? styles.colors.danger : key === 'high' ? styles.colors.warning : key === 'medium' ? '#F59E0B80' : styles.colors.success,
                  }} />
                  <span style={{ color: styles.colors.textMuted }}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Weekly Completion Trend */}
        <div style={{
          background: styles.colors.surface,
          padding: styles.spacing.cardPadding,
          borderRadius: styles.visualEffects.borderRadius,
          boxShadow: styles.visualEffects.shadowCard,
        }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: styles.colors.textMain, marginBottom: '1rem' }}>Weekly Completion Trend</h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.75rem', height: '120px', paddingTop: '1rem' }}>
            {[35, 45, 60, 40, 75, 55, 80].map((value, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{
                  width: '100%',
                  height: `${value}%`,
                  background: i === 6 ? styles.colors.primary : `${styles.colors.primary}60`,
                  borderRadius: '4px 4px 0 0',
                  transition: 'all 0.3s ease',
                }} />
                <span style={{ fontSize: '0.75rem', color: styles.colors.textMuted }}>{['M','T','W','T','F','S','S'][i]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{
        display: 'flex',
        gap: styles.spacing.elementGap,
        flexWrap: 'wrap',
      }}>
        <button
          onClick={onNewTask}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.875rem 1.5rem',
            background: styles.colors.primary,
            color: '#FFF',
            border: 'none',
            borderRadius: styles.visualEffects.borderRadius,
            fontSize: styles.typography.baseSize,
            fontWeight: 600,
            fontFamily: styles.typography.fontFamily,
            cursor: 'pointer',
            transition: styles.visualEffects.transition,
          }}
        >
          <Icons.Plus /> New Task
        </button>
        <button
          onClick={onNewIncident}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.875rem 1.5rem',
            background: styles.colors.danger,
            color: '#FFF',
            border: 'none',
            borderRadius: styles.visualEffects.borderRadius,
            fontSize: styles.typography.baseSize,
            fontWeight: 600,
            fontFamily: styles.typography.fontFamily,
            cursor: 'pointer',
            transition: styles.visualEffects.transition,
          }}
        >
          <Icons.Alert /> Log Incident
        </button>
      </div>
    </div>
  );
};

// Task List Screen Component
const TaskListScreen = ({ tasks, onEdit, onDelete, onNew }) => {
  const [filter, setFilter] = useState('all');

  const filteredTasks = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);

  const statusColors = {
    todo: { bg: '#F1F5F9', color: styles.colors.textMuted },
    in_progress: { bg: '#DBEAFE', color: styles.colors.primary },
    done: { bg: '#D1FAE5', color: styles.colors.success },
  };

  return (
    <div style={{
      padding: styles.spacing.containerPadding,
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: styles.typography.headingWeight,
          color: styles.colors.textMain,
        }}>Tasks</h1>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['all', 'todo', 'in_progress', 'done'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              style={{
                padding: '0.5rem 1rem',
                background: filter === status ? styles.colors.primary : styles.colors.surface,
                color: filter === status ? '#FFF' : styles.colors.textMuted,
                border: `1px solid ${filter === status ? styles.colors.primary : '#E2E8F0'}`,
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: '0.875rem',
                fontFamily: styles.typography.fontFamily,
                cursor: 'pointer',
                transition: styles.visualEffects.transition,
              }}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={onNew}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1.25rem',
          marginBottom: '1.5rem',
          background: styles.colors.primary,
          color: '#FFF',
          border: 'none',
          borderRadius: styles.visualEffects.borderRadius,
          fontSize: styles.typography.baseSize,
          fontWeight: 600,
          fontFamily: styles.typography.fontFamily,
          cursor: 'pointer',
        }}
      >
        <Icons.Plus /> Add Task
      </button>

      <div style={{
        background: styles.colors.surface,
        borderRadius: styles.visualEffects.borderRadius,
        boxShadow: styles.visualEffects.shadowCard,
        overflow: 'hidden',
      }}>
        {filteredTasks.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: styles.colors.textMuted }}>
            No tasks found. Create your first task!
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Title</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Status</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Due Date</th>
                <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => (
                <tr key={task.id} style={{ borderBottom: '1px solid #E2E8F0' }}>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: 500, color: styles.colors.textMain }}>{task.title}</div>
                    <div style={{ fontSize: '0.875rem', color: styles.colors.textMuted, marginTop: '0.25rem' }}>{task.description}</div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      background: statusColors[task.status].bg,
                      color: statusColors[task.status].color,
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: styles.colors.textMuted, fontSize: '0.875rem' }}>
                    {task.dueDate}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button
                      onClick={() => onEdit(task)}
                      style={{
                        padding: '0.5rem',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: styles.colors.textMuted,
                        marginRight: '0.5rem',
                      }}
                    >
                      <Icons.Edit />
                    </button>
                    <button
                      onClick={() => onDelete(task.id)}
                      style={{
                        padding: '0.5rem',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: styles.colors.danger,
                      }}
                    >
                      <Icons.Trash />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Task Form Modal Component
const TaskFormModal = ({ task, onSave, onClose }) => {
  const [formData, setFormData] = useState(task || {
    title: '',
    description: '',
    status: 'todo',
    dueDate: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title || !formData.dueDate) return;
    onSave(formData);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem',
    }}>
      <div style={{
        background: styles.colors.surface,
        borderRadius: styles.visualEffects.borderRadius,
        padding: '2rem',
        width: '100%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflow: 'auto',
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: styles.colors.textMain }}>
          {task ? 'Edit Task' : 'New Task'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #E2E8F0',
                  borderRadius: styles.visualEffects.borderRadius,
                  fontSize: styles.typography.baseSize,
                  fontFamily: styles.typography.fontFamily,
                  background: styles.colors.surface,
                  boxSizing: 'border-box',
                }}
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Due Date</label>
              <input
                type="date"
                value={formData.dueDate}
                onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #E2E8F0',
                  borderRadius: styles.visualEffects.borderRadius,
                  fontSize: styles.typography.baseSize,
                  fontFamily: styles.typography.fontFamily,
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'transparent',
                color: styles.colors.textMuted,
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontWeight: 500,
                fontFamily: styles.typography.fontFamily,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: '0.75rem 1.5rem',
                background: styles.colors.primary,
                color: '#FFF',
                border: 'none',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontWeight: 600,
                fontFamily: styles.typography.fontFamily,
                cursor: 'pointer',
              }}
            >
              Save Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Incident List Screen Component
const IncidentListScreen = ({ incidents, onEdit, onDelete, onNew }) => {
  const severityColors = {
    critical: { bg: '#FEE2E2', color: styles.colors.danger },
    high: { bg: '#FEF3C7', color: styles.colors.warning },
    medium: { bg: '#FEF3C780', color: '#D97706' },
    low: { bg: '#D1FAE5', color: styles.colors.success },
  };

  return (
    <div style={{
      padding: styles.spacing.containerPadding,
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: styles.typography.headingWeight,
          color: styles.colors.textMain,
        }}>Incidents</h1>
      </div>

      <button
        onClick={onNew}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1.25rem',
          marginBottom: '1.5rem',
          background: styles.colors.danger,
          color: '#FFF',
          border: 'none',
          borderRadius: styles.visualEffects.borderRadius,
          fontSize: styles.typography.baseSize,
          fontWeight: 600,
          fontFamily: styles.typography.fontFamily,
          cursor: 'pointer',
        }}
      >
        <Icons.Alert /> Log Incident
      </button>

      <div style={{
        background: styles.colors.surface,
        borderRadius: styles.visualEffects.borderRadius,
        boxShadow: styles.visualEffects.shadowCard,
        overflow: 'hidden',
      }}>
        {incidents.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: styles.colors.textMuted }}>
            No incidents logged. Great job keeping things stable!
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Title</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Severity</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Status</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Created</th>
                <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id} style={{ borderBottom: '1px solid #E2E8F0' }}>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: 500, color: styles.colors.textMain }}>{incident.title}</div>
                    {incident.resolution && (
                      <div style={{ fontSize: '0.875rem', color: styles.colors.success, marginTop: '0.25rem' }}>
                        ✓ Resolved: {incident.resolution}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      background: severityColors[incident.severity].bg,
                      color: severityColors[incident.severity].color,
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}>
                      {incident.severity}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      background: incident.status === 'resolved' ? '#D1FAE5' : '#FEE2E2',
                      color: incident.status === 'resolved' ? styles.colors.success : styles.colors.danger,
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}>
                      {incident.status}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: styles.colors.textMuted, fontSize: '0.875rem' }}>
                    {incident.createdAt}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button
                      onClick={() => onEdit(incident)}
                      style={{
                        padding: '0.5rem',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: styles.colors.textMuted,
                        marginRight: '0.5rem',
                      }}
                    >
                      <Icons.Edit />
                    </button>
                    <button
                      onClick={() => onDelete(incident.id)}
                      style={{
                        padding: '0.5rem',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: styles.colors.danger,
                      }}
                    >
                      <Icons.Trash />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Incident Form Modal Component
const IncidentFormModal = ({ incident, onSave, onClose }) => {
  const [formData, setFormData] = useState(incident || {
    title: '',
    severity: 'medium',
    status: 'open',
    resolution: '',
    createdAt: new Date().toISOString().split('T')[0],
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title) return;
    onSave(formData);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem',
    }}>
      <div style={{
        background: styles.colors.surface,
        borderRadius: styles.visualEffects.borderRadius,
        padding: '2rem',
        width: '100%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflow: 'auto',
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: styles.colors.textMain }}>
          {incident ? 'Edit Incident' : 'Log Incident'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Severity</label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #E2E8F0',
                  borderRadius: styles.visualEffects.borderRadius,
                  fontSize: styles.typography.baseSize,
                  fontFamily: styles.typography.fontFamily,
                  background: styles.colors.surface,
                  boxSizing: 'border-box',
                }}
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #E2E8F0',
                  borderRadius: styles.visualEffects.borderRadius,
                  fontSize: styles.typography.baseSize,
                  fontFamily: styles.typography.fontFamily,
                  background: styles.colors.surface,
                  boxSizing: 'border-box',
                }}
              >
                <option value="open">Open</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: styles.colors.textMain }}>Resolution Notes</label>
            <textarea
              value={formData.resolution}
              onChange={(e) => setFormData({ ...formData, resolution: e.target.value })}
              rows={4}
              placeholder="How was this incident resolved?"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontFamily: styles.typography.fontFamily,
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'transparent',
                color: styles.colors.textMuted,
                border: '1px solid #E2E8F0',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontWeight: 500,
                fontFamily: styles.typography.fontFamily,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: '0.75rem 1.5rem',
                background: styles.colors.danger,
                color: '#FFF',
                border: 'none',
                borderRadius: styles.visualEffects.borderRadius,
                fontSize: styles.typography.baseSize,
                fontWeight: 600,
                fontFamily: styles.typography.fontFamily,
                cursor: 'pointer',
              }}
            >
              Save Incident
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Weekly Digest Screen Component
const DigestScreen = ({ tasks, incidents }) => {
  const [dateRange, setDateRange] = useState(7);

  const completedTasks = tasks.filter(t => t.status === 'done');
  const openIncidents = incidents.filter(i => i.status !== 'resolved');
  const resolvedIncidents = incidents.filter(i => i.status === 'resolved');

  const generateMarkdown = () => {
    const now = new Date();
    const startDate = new Date(now.getTime() - dateRange * 24 * 60 * 60 * 1000);
    
    const formatDate = (d) => d.toISOString().split('T')[0];
    
    let md = `# Weekly Operations Digest\n\n`;
    md += `**Period:** ${formatDate(startDate)} to ${formatDate(now)}\n`;
    md += `**Generated:** ${formatDate(now)}\n\n`;
    
    md += `## Summary\n\n`;
    md += `- **Tasks Completed:** ${completedTasks.length}\n`;
    md += `- **Open Incidents:** ${openIncidents.length}\n`;
    md += `- **Incidents Resolved:** ${resolvedIncidents.length}\n\n`;
    
    md += `## Completed Tasks\n\n`;
    if (completedTasks.length === 0) {
      md += `_No tasks completed during this period._\n\n`;
    } else {
      completedTasks.forEach(task => {
        md += `- [x] **${task.title}**\n`;
        md += `  - Due: ${task.dueDate}\n`;
        if (task.description) md += `  - ${task.description}\n`;
        md += `\n`;
      });
    }
    
    md += `## Open Incidents (Risks)\n\n`;
    if (openIncidents.length === 0) {
      md += `_No open incidents. Great job!_\n\n`;
    } else {
      openIncidents.forEach(incident => {
        md += `- **[${incident.severity.toUpperCase()}]** ${incident.title}\n`;
        md += `  - Created: ${incident.createdAt}\n`;
        md += `  - Status: ${incident.status}\n`;
        md += `\n`;
      });
    }
    
    md += `## Incident Recap\n\n`;
    if (resolvedIncidents.length === 0) {
      md += `_No incidents resolved during this period._\n\n`;
    } else {
      resolvedIncidents.forEach(incident => {
        md += `- **${incident.title}**\n`;
        md += `  - Severity: ${incident.severity}\n`;
        md += `  - Resolution: ${incident.resolution || 'N/A'}\n`;
        md += `\n`;
      });
    }
    
    md += `---\n\n*Generated by OpsTracker*`;
    
    return md;
  };

  const downloadMarkdown = () => {
    const md = generateMarkdown();
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ops-digest-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      padding: styles.spacing.containerPadding,
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: styles.typography.headingWeight,
          color: styles.colors.textMain,
        }}>Weekly Digest</h1>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ color: styles.colors.textMuted, fontSize: '0.875rem' }}>Date Range:</label>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value))}
            style={{
              padding: '0.5rem 1rem',
              border: '1px solid #E2E8F0',
              borderRadius: styles.visualEffects.borderRadius,
              fontSize: styles.typography.baseSize,
              fontFamily: styles.typography.fontFamily,
              background: styles.colors.surface,
            }}
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'flex-end',
        marginBottom: '1.5rem',
      }}>
        <button
          onClick={downloadMarkdown}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.25rem',
            background: styles.colors.primary,
            color: '#FFF',
            border: 'none',
            borderRadius: styles.visualEffects.borderRadius,
            fontSize: styles.typography.baseSize,
            fontWeight: 600,
            fontFamily: styles.typography.fontFamily,
            cursor: 'pointer',
          }}
        >
          <Icons.Download /> Download Markdown
        </button>
      </div>

      <div style={{
        background: styles.colors.surface,
        borderRadius: styles.visualEffects.borderRadius,
        boxShadow: styles.visualEffects.shadowCard,
        padding: styles.spacing.cardPadding,
      }}>
        <div style={{
          background: '#F8FAFC',
          padding: '1rem',
          borderRadius: styles.visualEffects.borderRadius,
          marginBottom: '1rem',
          border: '1px solid #E2E8F0',
        }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: styles.colors.textMuted, marginBottom: '0.5rem' }}>PREVIEW</h3>
        </div>
        <pre style={{
          whiteSpace: 'pre-wrap',
          fontFamily: 'Monaco, Consolas, monospace',
          fontSize: '0.875rem',
          color: styles.colors.textMain,
          lineHeight: 1.6,
          margin: 0,
        }}>{generateMarkdown()}</pre>
      </div>
    </div>
  );
};

// Main App Component
export default function App() {
  const [user, setUser] = useState(null);
  const [currentScreen, setCurrentScreen] = useState('dashboard');
  const [tasks, setTasks] = useState(() => getStoredData('ops-tasks', initialTasks));
  const [incidents, setIncidents] = useState(() => getStoredData('ops-incidents', initialIncidents));
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [editingIncident, setEditingIncident] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Persist data to localStorage
  useEffect(() => {
    setStoredData('ops-tasks', tasks);
  }, [tasks]);

  useEffect(() => {
    setStoredData('ops-incidents', incidents);
  }, [incidents]);

  // Task handlers
  const handleNewTask = () => {
    setEditingTask(null);
    setShowTaskModal(true);
  };

  const handleEditTask = (task) => {
    setEditingTask(task);
    setShowTaskModal(true);
  };

  const handleSaveTask = (taskData) => {
    if (editingTask) {
      setTasks(tasks.map(t => t.id === editingTask.id ? { ...taskData, id: t.id } : t));
    } else {
      setTasks([...tasks, { ...taskData, id: Date.now() }]);
    }
    setShowTaskModal(false);
    setEditingTask(null);
  };

  const handleDeleteTask = (id) => {
    setTasks(tasks.filter(t => t.id !== id));
  };

  // Incident handlers
  const handleNewIncident = () => {
    setEditingIncident(null);
    setShowIncidentModal(true);
  };

  const handleEditIncident = (incident) => {
    setEditingIncident(incident);
    setShowIncidentModal(true);
  };

  const handleSaveIncident = (incidentData) => {
    if (editingIncident) {
      setIncidents(incidents.map(i => i.id === editingIncident.id ? { ...incidentData, id: i.id } : i));
    } else {
      setIncidents([...incidents, { ...incidentData, id: Date.now() }]);
    }
    setShowIncidentModal(false);
    setEditingIncident(null);
  };

  const handleDeleteIncident = (id) => {
    setIncidents(incidents.filter(i => i.id !== id));
  };

  // Auth handlers
  const handleLogin = (userData) => {
    setUser(userData);
    setStoredData('ops-user', userData);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('ops-user');
  };

  // Check for existing session
  useEffect(() => {
    const storedUser = getStoredData('ops-user', null);
    if (storedUser) {
      setUser(storedUser);
    }
  }, []);

  if (!user) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  const renderScreen = () => {
    switch (currentScreen) {
      case 'dashboard':
        return (
          <DashboardScreen
            tasks={tasks}
            incidents={incidents}
            onNewTask={handleNewTask}
            onNewIncident={handleNewIncident}
          />
        );
      case 'tasks':
        return (
          <TaskListScreen
            tasks={tasks}
            onEdit={handleEditTask}
            onDelete={handleDeleteTask}
            onNew={handleNewTask}
          />
        );
      case 'incidents':
        return (
          <IncidentListScreen
            incidents={incidents}
            onEdit={handleEditIncident}
            onDelete={handleDeleteIncident}
            onNew={handleNewIncident}
          />
        );
      case 'digest':
        return <DigestScreen tasks={tasks} incidents={incidents} />;
      default:
        return null;
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: styles.colors.background,
      fontFamily: styles.typography.fontFamily,
    }}>
      <Sidebar
        currentScreen={currentScreen}
        setScreen={setCurrentScreen}
        onLogout={handleLogout}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
      />

      <main style={{
        marginLeft: '260px',
        minHeight: '100vh',
      }}>
        <style>{`
          @media (max-width: 768px) {
            main { margin-left: 0; }
          }
        `}</style>
        {renderScreen()}
      </main>

      {showTaskModal && (
        <TaskFormModal
          task={editingTask}
          onSave={handleSaveTask}
          onClose={() => {
            setShowTaskModal(false);
            setEditingTask(null);
          }}
        />
      )}

      {showIncidentModal && (
        <IncidentFormModal
          incident={editingIncident}
          onSave={handleSaveIncident}
          onClose={() => {
            setShowIncidentModal(false);
            setEditingIncident(null);
          }}
        />
      )}
    </div>
  );
}
