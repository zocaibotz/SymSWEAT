import React, { useState, useEffect } from 'react';

// Style tokens from UX spec
const styles = {
  colors: {
    primary: '#6366F1',
    primary_dark: '#4F46E5',
    primary_light: '#818CF8',
    secondary: '#06B6D4',
    secondary_dark: '#0891B2',
    accent: '#F59E0B',
    accent_dark: '#D97706',
    background_dark: '#0F172A',
    background_card: '#1E293B',
    background_elevated: '#334155',
    surface: '#1E293B',
    text_primary: '#F8FAFC',
    text_secondary: '#94A3B8',
    text_muted: '#64748B',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    border: '#334155',
  },
  typography: {
    font_family_heading: 'Inter, system-ui, sans-serif',
    font_family_body: 'Inter, system-ui, sans-serif',
    font_family_mono: 'JetBrains Mono, monospace',
    heading_1: '32px',
    heading_2: '24px',
    heading_3: '20px',
    body_large: '18px',
    body: '16px',
    body_small: '14px',
    caption: '12px',
    button: '14px',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  border_radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px rgba(0,0,0,0.3)',
    md: '0 4px 6px rgba(0,0,0,0.4)',
    lg: '0 10px 15px rgba(0,0,0,0.5)',
    glow_primary: '0 0 20px rgba(99,102,241,0.4)',
    glow_secondary: '0 0 20px rgba(6,182,212,0.4)',
  },
  status_colors: {
    not_started: '#64748B',
    in_progress: '#3B82F6',
    done: '#10B981',
    blocked: '#EF4444',
  },
};

// Initial mock data
const initialIdeas = [
  { id: 1, title: 'Build MVP for task app', description: 'Create a minimal viable product for solo founders', impact: 8, effort: 6, urgency: 7, createdAt: new Date().toISOString() },
  { id: 2, title: 'Set up marketing funnel', description: 'Design and implement email capture and nurture sequence', impact: 7, effort: 5, urgency: 6, createdAt: new Date().toISOString() },
  { id: 3, title: 'Launch beta waitlist', description: 'Create landing page and collect early adopter emails', impact: 9, effort: 3, urgency: 8, createdAt: new Date().toISOString() },
];

const initialMissions = [
  { id: 1, ideaId: 3, title: 'Launch beta waitlist', description: 'Create landing page and collect early adopter emails', subtasks: [
    { id: 1, title: 'Design landing page wireframe', status: 'done' },
    { id: 2, title: 'Write copy for hero section', status: 'in_progress' },
    { id: 3, title: 'Set up email capture form', status: 'not_started' },
    { id: 4, title: 'Deploy to production', status: 'not_started', blocker: 'Need domain' },
  ]},
  { id: 2, ideaId: 1, title: 'Build MVP for task app', description: 'Create a minimal viable product for solo founders', subtasks: [
    { id: 1, title: 'Create database schema', status: 'done' },
    { id: 2, title: 'Build authentication flow', status: 'in_progress' },
    { id: 3, title: 'Implement task CRUD', status: 'not_started' },
  ]},
  { id: 3, ideaId: 2, title: 'Set up marketing funnel', description: 'Design and implement email capture and nurture sequence', subtasks: [
    { id: 1, title: 'Research email marketing tools', status: 'not_started' },
    { id: 2, title: 'Create lead magnet content', status: 'not_started' },
    { id: 3, title: 'Design automation workflow', status: 'not_started' },
  ]},
];

// Components
const Button = ({ children, onClick, variant = 'primary', style = {}, disabled = false }) => {
  const baseStyle = {
    padding: '12px 24px',
    borderRadius: styles.border_radius.md,
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: styles.typography.button,
    fontWeight: 600,
    letterSpacing: '0.04em',
    transition: 'all 150ms ease',
    opacity: disabled ? 0.5 : 1,
    ...style,
  };

  const variants = {
    primary: {
      background: styles.colors.primary,
      color: styles.colors.text_primary,
      boxShadow: styles.shadows.glow_primary,
    },
    secondary: {
      background: styles.colors.secondary,
      color: styles.colors.text_primary,
      boxShadow: styles.shadows.glow_secondary,
    },
    outline: {
      background: 'transparent',
      color: styles.colors.text_primary,
      border: `1px solid ${styles.colors.border}`,
    },
    ghost: {
      background: 'transparent',
      color: styles.colors.text_secondary,
    },
    danger: {
      background: styles.colors.error,
      color: styles.colors.text_primary,
    },
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{ ...baseStyle, ...variants[variant] }}
    >
      {children}
    </button>
  );
};

const Input = ({ label, value, onChange, placeholder, type = 'text', required = false }) => {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: styles.spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: styles.spacing.xs,
          color: styles.colors.text_secondary,
          fontSize: styles.typography.body_small,
          fontWeight: 500,
        }}>
          {label} {required && <span style={{ color: styles.colors.error }}>*</span>}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          width: '100%',
          padding: '12px 16px',
          borderRadius: styles.border_radius.md,
          border: `1px solid ${focused ? styles.colors.primary : styles.colors.border}`,
          background: styles.colors.background_elevated,
          color: styles.colors.text_primary,
          fontSize: styles.typography.body,
          outline: 'none',
          transition: 'border-color 150ms ease',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
};

const TextArea = ({ label, value, onChange, placeholder, rows = 4 }) => {
  return (
    <div style={{ marginBottom: styles.spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: styles.spacing.xs,
          color: styles.colors.text_secondary,
          fontSize: styles.typography.body_small,
          fontWeight: 500,
        }}>
          {label}
        </label>
      )}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        style={{
          width: '100%',
          padding: '12px 16px',
          borderRadius: styles.border_radius.md,
          border: `1px solid ${styles.colors.border}`,
          background: styles.colors.background_elevated,
          color: styles.colors.text_primary,
          fontSize: styles.typography.body,
          fontFamily: styles.typography.font_family_body,
          outline: 'none',
          resize: 'vertical',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
};

const Card = ({ children, style = {}, onClick, hoverable = false }) => {
  const [isHovered, setIsHovered] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: styles.colors.background_card,
        borderRadius: styles.border_radius.lg,
        padding: styles.spacing.lg,
        border: `1px solid ${styles.colors.border}`,
        transition: 'all 150ms ease',
        transform: isHovered && hoverable ? 'translateY(-2px)' : 'none',
        boxShadow: isHovered && hoverable ? styles.shadows.md : styles.shadows.sm,
        cursor: hoverable ? 'pointer' : 'default',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const Badge = ({ children, variant = 'default' }) => {
  const colors = {
    default: { bg: styles.colors.text_muted + '33', color: styles.colors.text_secondary },
    success: { bg: styles.colors.success + '33', color: styles.colors.success },
    warning: { bg: styles.colors.warning + '33', color: styles.colors.warning },
    error: { bg: styles.colors.error + '33', color: styles.colors.error },
    info: { bg: styles.colors.info + '33', color: styles.colors.info },
  };
  return (
    <span style={{
      display: 'inline-block',
      padding: `${styles.spacing.xs} ${styles.spacing.sm}`,
      borderRadius: styles.border_radius.full,
      fontSize: styles.typography.caption,
      fontWeight: 500,
      background: colors[variant].bg,
      color: colors[variant].color,
    }}>
      {children}
    </span>
  );
};

const StatusIndicator = ({ status }) => {
  const statusConfig = {
    not_started: { label: 'Not Started', color: styles.status_colors.not_started },
    in_progress: { label: 'In Progress', color: styles.status_colors.in_progress },
    done: { label: 'Done', color: styles.status_colors.done },
    blocked: { label: 'Blocked', color: styles.status_colors.blocked },
  };
  const config = statusConfig[status];
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: styles.spacing.xs,
      color: config.color,
      fontSize: styles.typography.caption,
      fontWeight: 500,
    }}>
      <span style={{
        width: 8,
        height: 8,
        borderRadius: styles.border_radius.full,
        background: config.color,
      }} />
      {config.label}
    </span>
  );
};

const Slider = ({ label, value, onChange, min = 1, max = 10 }) => {
  return (
    <div style={{ marginBottom: styles.spacing.md }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: styles.spacing.xs,
      }}>
        <label style={{
          color: styles.colors.text_secondary,
          fontSize: styles.typography.body_small,
          fontWeight: 500,
        }}>{label}</label>
        <span style={{
          color: styles.colors.primary,
          fontSize: styles.typography.body_small,
          fontWeight: 600,
        }}>{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        style={{
          width: '100%',
          height: 6,
          borderRadius: styles.border_radius.full,
          appearance: 'none',
          background: `linear-gradient(to right, ${styles.colors.primary} 0%, ${styles.colors.primary} ${((value - min) / (max - min)) * 100}%, ${styles.colors.border} ${((value - min) / (max - min)) * 100}%, ${styles.colors.border} 100%)`,
          cursor: 'pointer',
        }}
      />
    </div>
  );
};

// Screen Components
const AuthScreen = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
, setPassword]  const [password = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setError('');
    onLogin();
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: styles.colors.background_dark,
      padding: styles.spacing.md,
    }}>
      <Card style={{ maxWidth: 400, width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: styles.spacing.xl }}>
          <h1 style={{
            fontSize: styles.typography.heading_1,
            fontWeight: 700,
            color: styles.colors.text_primary,
            marginBottom: styles.spacing.xs,
          }}>
            FounderFlow
          </h1>
          <p style={{
            color: styles.colors.text_secondary,
            fontSize: styles.typography.body,
          }}>
            {isLogin ? 'Welcome back!' : 'Start your journey'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{
              padding: styles.spacing.sm,
              borderRadius: styles.border_radius.md,
              background: styles.colors.error + '22',
              color: styles.colors.error,
              marginBottom: styles.spacing.md,
              fontSize: styles.typography.body_small,
            }}>
              {error}
            </div>
          )}
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="you@example.com"
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="••••••••"
            required
          />
          <Button
            onClick={handleSubmit}
            style={{ width: '100%', marginTop: styles.spacing.md }}
          >
            {isLogin ? 'Sign In' : 'Create Account'}
          </Button>
        </form>

        <p style={{
          textAlign: 'center',
          marginTop: styles.spacing.lg,
          color: styles.colors.text_secondary,
          fontSize: styles.typography.body_small,
        }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            style={{
              background: 'none',
              border: 'none',
              color: styles.colors.primary,
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </Card>
    </div>
  );
};

const IdeaCaptureModal = ({ onClose, onSave }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleSave = () => {
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    onSave({ title, description, createdAt: new Date().toISOString() });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: styles.spacing.md,
      zIndex: 100,
    }}>
      <Card style={{ maxWidth: 500, width: '100%' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: styles.spacing.lg,
        }}>
          <h2 style={{
            fontSize: styles.typography.heading_2,
            fontWeight: 600,
            color: styles.colors.text_primary,
          }}>
            Capture Idea
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: styles.colors.text_secondary,
              cursor: 'pointer',
              fontSize: 24,
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div style={{
            padding: styles.spacing.sm,
            borderRadius: styles.border_radius.md,
            background: styles.colors.error + '22',
            color: styles.colors.error,
            marginBottom: styles.spacing.md,
            fontSize: styles.typography.body_small,
          }}>
            {error}
          </div>
        )}

        <Input
          label="Title"
          value={title}
          onChange={setTitle}
          placeholder="What's your idea?"
          required
        />
        <TextArea
          label="Description (optional)"
          value={description}
          onChange={setDescription}
          placeholder="Add more details..."
        />
        <div style={{
          display: 'flex',
          gap: styles.spacing.sm,
          justifyContent: 'flex-end',
        }}>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave}>Save Idea</Button>
        </div>
      </Card>
    </div>
  );
};

const PrioritizationScreen = ({ ideas, onUpdateIdea, onGenerateMissions }) => {
  const getScore = (idea) => {
    return Math.round((idea.impact * 0.4 + (11 - idea.effort) * 0.3 + idea.urgency * 0.3));
  };

  const sortedIdeas = [...ideas].sort((a, b) => getScore(b) - getScore(a));

  return (
    <div style={{ padding: styles.spacing.lg }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: styles.spacing.lg,
      }}>
        <h1 style={{
          fontSize: styles.typography.heading_1,
          fontWeight: 700,
          color: styles.colors.text_primary,
        }}>
          Prioritize Ideas
        </h1>
        <Button onClick={onGenerateMissions}>
          Generate Missions →
        </Button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: styles.spacing.md }}>
        {sortedIdeas.map((idea, index) => (
          <Card key={idea.id}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: styles.spacing.md,
            }}>
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: styles.spacing.sm,
                }}>
                  <span style={{
                    width: 24,
                    height: 24,
                    borderRadius: styles.border_radius.full,
                    background: styles.colors.primary,
                    color: styles.colors.text_primary,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: styles.typography.body_small,
                    fontWeight: 600,
                  }}>
                    {index + 1}
                  </span>
                  <h3 style={{
                    fontSize: styles.typography.heading_3,
                    fontWeight: 600,
                    color: styles.colors.text_primary,
                  }}>
                    {idea.title}
                  </h3>
                </div>
                <p style={{
                  color: styles.colors.text_secondary,
                  fontSize: styles.typography.body_small,
                  marginTop: styles.spacing.xs,
                  marginLeft: 32,
                }}>
                  {idea.description}
                </p>
              </div>
              <Badge variant="info">Score: {getScore(idea)}</Badge>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: styles.spacing.lg,
            }}>
              <Slider
                label="Impact"
                value={idea.impact}
                onChange={(v) => onUpdateIdea(idea.id, { impact: v })}
              />
              <Slider
                label="Effort"
                value={idea.effort}
                onChange={(v) => onUpdateIdea(idea.id, { effort: v })}
              />
              <Slider
                label="Urgency"
                value={idea.urgency}
                onChange={(v) => onUpdateIdea(idea.id, { urgency: v })}
              />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

const MissionBoard = ({ missions, onMissionClick, onAddIdea, showAddButton = true }) => {
  const getWeekNumber = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now - start;
    const oneWeek = 604800000;
    return Math.ceil((diff + start.getDay() * 86400000) / oneWeek);
  };

  const getProgress = (mission) => {
    const done = mission.subtasks.filter(t => t.status === 'done').length;
    return Math.round((done / mission.subtasks.length) * 100);
  };

  return (
    <div style={{ padding: styles.spacing.lg }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: styles.spacing.xl,
      }}>
        <div>
          <h1 style={{
            fontSize: styles.typography.heading_1,
            fontWeight: 700,
            color: styles.colors.text_primary,
            marginBottom: styles.spacing.xs,
          }}>
            Mission Board
          </h1>
          <p style={{
            color: styles.colors.text_secondary,
            fontSize: styles.typography.body,
          }}>
            Week {getWeekNumber()} • Your top priorities
          </p>
        </div>
        {showAddButton && (
          <Button onClick={onAddIdea}>+ New Idea</Button>
        )}
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: styles.spacing.lg,
      }}>
        {missions.map((mission, index) => (
          <Card
            key={mission.id}
            hoverable
            onClick={() => onMissionClick(mission)}
            style={{
              borderTop: `4px solid ${
                index === 0 ? styles.colors.accent :
                index === 1 ? styles.colors.secondary :
                styles.colors.primary
              }`,
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: styles.spacing.md,
            }}>
              <Badge>
                {index === 0 ? '🏆 Priority 1' :
                 index === 1 ? '⭐ Priority 2' :
                 '💪 Priority 3'}
              </Badge>
              <span style={{
                color: styles.colors.text_muted,
                fontSize: styles.typography.caption,
              }}>
                {getProgress(mission)}% done
              </span>
            </div>
            <h3 style={{
              fontSize: styles.typography.heading_3,
              fontWeight: 600,
              color: styles.colors.text_primary,
              marginBottom: styles.spacing.sm,
            }}>
              {mission.title}
            </h3>
            <p style={{
              color: styles.colors.text_secondary,
              fontSize: styles.typography.body_small,
              marginBottom: styles.spacing.md,
            }}>
              {mission.description}
            </p>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: styles.spacing.sm,
            }}>
              <div style={{
                flex: 1,
                height: 6,
                borderRadius: styles.border_radius.full,
                background: styles.colors.border,
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${getProgress(mission)}%`,
                  height: '100%',
                  background: styles.colors.success,
                  borderRadius: styles.border_radius.full,
                  transition: 'width 500ms ease-out',
                }} />
              </div>
              <span style={{
                color: styles.colors.text_muted,
                fontSize: styles.typography.caption,
              }}>
                {mission.subtasks.filter(t => t.status === 'done').length}/{mission.subtasks.length}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

const MissionDetail = ({ mission, onUpdateTask, onBack, onAddSubtask }) => {
  const [newSubtask, setNewSubtask] = useState('');
  const [showAddSubtask, setShowAddSubtask] = useState(false);

  const handleAddSubtask = () => {
    if (newSubtask.trim()) {
      onAddSubtask(mission.id, newSubtask);
      setNewSubtask('');
      setShowAddSubtask(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'done': return '✅';
      case 'in_progress': return '🔄';
      case 'blocked': return '🚫';
      default: return '⭕';
    }
  };

  const cycleStatus = (currentStatus) => {
    const cycle = ['not_started', 'in_progress', 'done'];
    const idx = cycle.indexOf(currentStatus);
    return cycle[(idx + 1) % cycle.length];
  };

  return (
    <div style={{ padding: styles.spacing.lg }}>
      <button
        onClick={onBack}
        style={{
          background: 'none',
          border: 'none',
          color: styles.colors.text_secondary,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: styles.spacing.xs,
          marginBottom: styles.spacing.lg,
          fontSize: styles.typography.body,
        }}
      >
        ← Back to Mission Board
      </button>

      <Card style={{ marginBottom: styles.spacing.lg }}>
        <h1 style={{
          fontSize: styles.typography.heading_1,
          fontWeight: 700,
          color: styles.colors.text_primary,
          marginBottom: styles.spacing.sm,
        }}>
          {mission.title}
        </h1>
        <p style={{
          color: styles.colors.text_secondary,
          fontSize: styles.typography.body,
          marginBottom: styles.spacing.lg,
        }}>
          {mission.description}
        </p>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h3 style={{
            fontSize: styles.typography.heading_3,
            fontWeight: 600,
            color: styles.colors.text_primary,
          }}>
            Subtasks ({mission.subtasks.length})
          </h3>
          <Button variant="outline" onClick={() => setShowAddSubtask(!showAddSubtask)}>
            + Add Subtask
          </Button>
        </div>

        {showAddSubtask && (
          <div style={{
            display: 'flex',
            gap: styles.spacing.sm,
            marginTop: styles.spacing.md,
            marginBottom: styles.spacing.md,
          }}>
            <Input
              value={newSubtask}
              onChange={setNewSubtask}
              placeholder="New subtask..."
              style={{ flex: 1 }}
            />
            <Button onClick={handleAddSubtask}>Add</Button>
          </div>
        )}
      </Card>

      <div style={{ display: 'flex', flexDirection: 'column', gap: styles.spacing.sm }}>
        {mission.subtasks.map((task) => (
          <Card key={task.id} style={{ padding: styles.spacing.md }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: styles.spacing.md,
            }}>
              <button
                onClick={() => onUpdateTask(mission.id, task.id, { status: cycleStatus(task.status) })}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: 20,
                  cursor: 'pointer',
                }}
              >
                {getStatusIcon(task.status)}
              </button>
              <div style={{ flex: 1 }}>
                <span style={{
                  color: task.status === 'done' ? styles.colors.text_muted : styles.colors.text_primary,
                  fontSize: styles.typography.body,
                  textDecoration: task.status === 'done' ? 'line-through' : 'none',
                }}>
                  {task.title}
                </span>
                {task.blocker && (
                  <div style={{
                    marginTop: styles.spacing.xs,
                    padding: styles.spacing.xs,
                    borderRadius: styles.border_radius.sm,
                    background: styles.colors.error + '22',
                    color: styles.colors.error,
                    fontSize: styles.typography.caption,
                  }}>
                    🚫 Blocked: {task.blocker}
                  </div>
                )}
              </div>
              <StatusIndicator status={task.status} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

const ProgressRadar = ({ missions, onNavigate }) => {
  const allTasks = missions.flatMap(m => m.subtasks);
  const stats = {
    not_started: allTasks.filter(t => t.status === 'not_started').length,
    in_progress: allTasks.filter(t => t.status === 'in_progress').length,
    done: allTasks.filter(t => t.status === 'done').length,
    blocked: allTasks.filter(t => t.status === 'blocked').length,
  };
  const total = allTasks.length;
  const completionRate = total ? Math.round((stats.done / total) * 100) : 0;

  // Mock trend data
  const trendData = [
    { week: 'W1', rate: 45 },
    { week: 'W2', rate: 62 },
    { week: 'W3', rate: 58 },
    { week: 'W4', rate: completionRate },
  ];
  const maxRate = Math.max(...trendData.map(d => d.rate));

  const statusCards = [
    { status: 'not_started', label: 'Not Started', count: stats.not_started, color: styles.status_colors.not_started },
    { status: 'in_progress', label: 'In Progress', count: stats.in_progress, color: styles.status_colors.in_progress },
    { status: 'done', label: 'Done', count: stats.done, color: styles.status_colors.done },
    { status: 'blocked', label: 'Blocked', count: stats.blocked, color: styles.status_colors.blocked },
  ];

  return (
    <div style={{ padding: styles.spacing.lg }}>
      <h1 style={{
        fontSize: styles.typography.heading_1,
        fontWeight: 700,
        color: styles.colors.text_primary,
        marginBottom: styles.spacing.xl,
      }}>
        Progress Radar
      </h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: styles.spacing.lg,
        marginBottom: styles.spacing.xl,
      }}>
        {statusCards.map(({ status, label, count, color }) => (
          <Card key={status}>
            <div style={{
              fontSize: styles.typography.heading_1,
              fontWeight: 700,
              color: color,
              marginBottom: styles.spacing.xs,
            }}>
              {count}
            </div>
            <div style={{
              color: styles.colors.text_secondary,
              fontSize: styles.typography.body,
            }}>
              {label}
            </div>
          </Card>
        ))}
      </div>

      <Card style={{ marginBottom: styles.spacing.xl }}>
        <h3 style={{
          fontSize: styles.typography.heading_3,
          fontWeight: 600,
          color: styles.colors.text_primary,
          marginBottom: styles.spacing.lg,
        }}>
          Confidence Trend (4 Weeks)
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: styles.spacing.lg,
          height: 200,
        }}>
          {trendData.map((d, i) => (
            <div key={i} style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: styles.spacing.sm,
            }}>
              <div style={{
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                height: 160,
              }}>
                <span style={{
                  color: styles.colors.primary,
                  fontWeight: 600,
                  fontSize: styles.typography.body_small,
                }}>
                  {d.rate}%
                </span>
                <div style={{
                  width: '60%',
                  height: `${(d.rate / maxRate) * 140}px`,
                  background: `linear-gradient(to top, ${styles.colors.primary}, ${styles.colors.primary_light})`,
                  borderRadius: `${styles.border_radius.md} ${styles.border_radius.md} 0 0`,
                  transition: 'height 500ms ease-out',
                }} />
              </div>
              <span style={{
                color: styles.colors.text_muted,
                fontSize: styles.typography.caption,
              }}>
                {d.week}
              </span>
            </div>
          ))}
        </div>
      </Card>

      <div style={{
        display: 'flex',
        justifyContent: 'center',
      }}>
        <Button onClick={() => onNavigate('reflection')}>
          Weekly Reflection →
        </Button>
      </div>
    </div>
  );
};

const ReflectionScreen = ({ onNavigate }) => {
  const [wentWell, setWentWell] = useState('');
  const [didntGoWell, setDidntGoWell] = useState('');
  const [saved, setSaved] = useState(false);

  const suggestedActions = [
    'Review and prioritize remaining tasks',
    'Schedule focus time for deep work',
    'Reach out to potential early adopters',
    'Analyze conversion metrics from last week',
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ padding: styles.spacing.lg }}>
      <h1 style={{
        fontSize: styles.typography.heading_1,
        fontWeight: 700,
        color: styles.colors.text_primary,
        marginBottom: styles.spacing.xl,
      }}>
        Weekly Reflection
      </h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: styles.spacing.lg,
        marginBottom: styles.spacing.xl,
      }}>
        <Card>
          <h3 style={{
            fontSize: styles.typography.heading_3,
            fontWeight: 600,
            color: styles.colors.success,
            marginBottom: styles.spacing.md,
          }}>
            ✅ What went well
          </h3>
          <TextArea
            value={wentWell}
            onChange={setWentWell}
            placeholder="Celebrate your wins this week..."
            rows={6}
          />
        </Card>

        <Card>
          <h3 style={{
            fontSize: styles.typography.heading_3,
            fontWeight: 600,
            color: styles.colors.error,
            marginBottom: styles.spacing.md,
          }}>
            ❌ What didn't go well
          </h3>
          <TextArea
            value={didntGoWell}
            onChange={setDidntGoWell}
            placeholder="Identify challenges and learnings..."
            rows={6}
          />
        </Card>
      </div>

      <Card style={{ marginBottom: styles.spacing.xl }}>
        <h3 style={{
          fontSize: styles.typography.heading_3,
          fontWeight: 600,
          color: styles.colors.text_primary,
          marginBottom: styles.spacing.md,
        }}>
          💡 Suggested next actions
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: styles.spacing.sm }}>
          {suggestedActions.map((action, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: styles.spacing.sm,
              color: styles.colors.text_secondary,
              fontSize: styles.typography.body,
            }}>
              <span style={{ color: styles.colors.accent }}>▸</span>
              {action}
            </div>
          ))}
        </div>
      </Card>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <Button variant="ghost" onClick={() => onNavigate('radar')}>
          ← Back to Progress
        </Button>
        <div style={{ display: 'flex', gap: styles.spacing.sm, alignItems: 'center' }}>
          {saved && (
            <span style={{ color: styles.colors.success, fontWeight: 600 }}>
              ✓ Reflection saved!
            </span>
          )}
          <Button onClick={handleSave}>Save Reflection</Button>
        </div>
      </div>
    </div>
  );
};

const Navigation = ({ currentScreen, onNavigate }) => {
  const navItems = [
    { id: 'missions', label: 'Missions', icon: '🎯' },
    { id: 'prioritize', label: 'Prioritize', icon: '📊' },
    { id: 'radar', label: 'Progress', icon: '📈' },
    { id: 'reflection', label: 'Reflect', icon: '🔮' },
  ];

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: styles.colors.background_card,
      borderTop: `1px solid ${styles.colors.border}`,
      padding: `${styles.spacing.sm} ${styles.spacing.md}`,
      display: 'flex',
      justifyContent: 'center',
      gap: styles.spacing.xs,
      zIndex: 50,
    }}>
      {navItems.map((item) => (
        <button
          key={item.id}
          onClick={() => onNavigate(item.id)}
          style={{
            background: currentScreen === item.id ? styles.colors.primary + '22' : 'transparent',
            border: 'none',
            borderRadius: styles.border_radius.md,
            padding: `${styles.spacing.sm} ${styles.spacing.md}`,
            color: currentScreen === item.id ? styles.colors.primary : styles.colors.text_secondary,
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: styles.spacing.xs,
            transition: 'all 150ms ease',
            minWidth: 80,
          }}
        >
          <span style={{ fontSize: 20 }}>{item.icon}</span>
          <span style={{
            fontSize: styles.typography.caption,
            fontWeight: currentScreen === item.id ? 600 : 400,
          }}>
            {item.label}
          </span>
        </button>
      ))}
    </nav>
  );
};

// Main App Component
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentScreen, setCurrentScreen] = useState('missions');
  const [ideas, setIdeas] = useState(initialIdeas);
  const [missions, setMissions] = useState(initialMissions);
  const [selectedMission, setSelectedMission] = useState(null);
  const [showIdeaModal, setShowIdeaModal] = useState(false);

  // Calculate missions from top 3 ideas
  const generateMissions = () => {
    const scoredIdeas = ideas.map(idea => ({
      ...idea,
      score: idea.impact * 0.4 + (11 - idea.effort) * 0.3 + idea.urgency * 0.3,
    })).sort((a, b) => b.score - a.score).slice(0, 3);

    const newMissions = scoredIdeas.map((idea, idx) => ({
      id: Date.now() + idx,
      ideaId: idea.id,
      title: idea.title,
      description: idea.description,
      subtasks: [
        { id: Date.now() + idx * 10 + 1, title: 'Research and planning', status: 'not_started' },
        { id: Date.now() + idx * 10 + 2, title: 'First draft / prototype', status: 'not_started' },
        { id: Date.now() + idx * 10 + 3, title: 'Review and refine', status: 'not_started' },
      ],
    }));

    setMissions(newMissions);
    setCurrentScreen('missions');
  };

  const handleAddIdea = (idea) => {
    const newIdea = {
      ...idea,
      id: Date.now(),
      impact: 5,
      effort: 5,
      urgency: 5,
    };
    setIdeas([...ideas, newIdea]);
  };

  const handleUpdateIdea = (id, updates) => {
    setIdeas(ideas.map(idea =>
      idea.id === id ? { ...idea, ...updates } : idea
    ));
  };

  const handleUpdateTask = (missionId, taskId, updates) => {
    setMissions(missions.map(mission =>
      mission.id === missionId ? {
        ...mission,
        subtasks: mission.subtasks.map(task =>
          task.id === taskId ? { ...task, ...updates } : task
        ),
      } : mission
    ));
  };

  const handleAddSubtask = (missionId, title) => {
    setMissions(missions.map(mission =>
      mission.id === missionId ? {
        ...mission,
        subtasks: [...mission.subtasks, {
          id: Date.now(),
          title,
          status: 'not_started',
        }],
      } : mission
    ));
  };

  if (!isAuthenticated) {
    return <AuthScreen onLogin={() => setIsAuthenticated(true)} />;
  }

  const renderScreen = () => {
    if (selectedMission) {
      return (
        <MissionDetail
          mission={selectedMission}
          onUpdateTask={handleUpdateTask}
          onBack={() => setSelectedMission(null)}
          onAddSubtask={handleAddSubtask}
        />
      );
    }

    switch (currentScreen) {
      case 'missions':
        return (
          <MissionBoard
            missions={missions}
            onMissionClick={setSelectedMission}
            onAddIdea={() => setShowIdeaModal(true)}
          />
        );
      case 'prioritize':
        return (
          <PrioritizationScreen
            ideas={ideas}
            onUpdateIdea={handleUpdateIdea}
            onGenerateMissions={generateMissions}
          />
        );
      case 'radar':
        return (
          <ProgressRadar
            missions={missions}
            onNavigate={setCurrentScreen}
          />
        );
      case 'reflection':
        return (
          <ReflectionScreen
            onNavigate={setCurrentScreen}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: styles.colors.background_dark,
      fontFamily: styles.typography.font_family_body,
      color: styles.colors.text_primary,
      paddingBottom: 80,
    }}>
      {renderScreen()}
      {!selectedMission && (
        <Navigation
          currentScreen={currentScreen}
          onNavigate={setCurrentScreen}
        />
      )}
      {showIdeaModal && (
        <IdeaCaptureModal
          onClose={() => setShowIdeaModal(false)}
          onSave={handleAddIdea}
        />
      )}
    </div>
  );
}
