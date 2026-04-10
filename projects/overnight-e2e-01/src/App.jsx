import React, { useState, useMemo } from 'react';

// --- Style Tokens ---
const tokens = {
  colors: {
    primary: '#4f46e5',
    primaryHover: '#4338ca',
    background: '#f9fafb',
    surface: '#ffffff',
    textMain: '#111827',
    textMuted: '#6b7280',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    border: '#e5e7eb',
  },
  typography: {
    fontSans: 'Inter, system-ui, -apple-system, sans-serif',
    sizeBase: '16px',
    sizeH1: '1.875rem',
    weightBold: '700',
    weightMedium: '500',
  },
  spacing: {
    containerPadding: '1.5rem',
    elementGap: '1rem',
    cardRadius: '0.75rem',
  },
  shadows: {
    card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    focus: '0 0 0 3px rgba(79, 70, 229, 0.2)',
  },
};

// --- Components ---

const Button = ({ children, variant = 'primary', ...props }) => {
  const style = {
    padding: '0.625rem 1.25rem',
    borderRadius: '0.5rem',
    fontSize: '0.875rem',
    fontWeight: tokens.typography.weightMedium,
    cursor: 'pointer',
    border: 'none',
    transition: 'background 0.2s',
    backgroundColor: variant === 'primary' ? tokens.colors.primary : 'transparent',
    color: variant === 'primary' ? 'white' : tokens.colors.textMuted,
    border: variant === 'outline' ? `1px solid ${tokens.colors.border}` : 'none',
    ...props.style,
  };
  return <button style={style} {...props}>{children}</button>;
};

const Card = ({ children, style = {} }) => (
  <div style={{
    backgroundColor: tokens.colors.surface,
    borderRadius: tokens.spacing.cardRadius,
    boxShadow: tokens.shadows.card,
    padding: '1.5rem',
    border: `1px solid ${tokens.colors.border}`,
    ...style
  }}>
    {children}
  </div>
);

const Input = ({ label, ...props }) => (
  <div style={{ marginBottom: '1rem' }}>
    {label && <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: tokens.typography.weightMedium, color: tokens.colors.textMain }}>{label}</label>}
    <input
      style={{
        width: '100%',
        padding: '0.625rem',
        borderRadius: '0.375rem',
        border: `1px solid ${tokens.colors.border}`,
        fontSize: tokens.typography.sizeBase,
        boxSizing: 'border-box',
      }}
      {...props}
    />
  </div>
);

export default function App() {
  const [view, setView] = useState('auth'); // auth, dashboard, inventory, editor
  const [isLogin, setIsLogin] = useState(true);
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Finish Project Proposal', description: 'Draft for the new client', tags: ['work', 'urgent'], dueDate: '2026-02-27', status: 'pending' },
    { id: 2, title: 'Grocery Shopping', description: 'Milk, Eggs, Bread', tags: ['personal'], dueDate: '2026-02-28', status: 'completed' },
  ]);
  const [search, setSearch] = useState('');
  const [editingTask, setEditingTask] = useState(null);

  // Auth Handlers
  const handleAuth = (e) => {
    e.preventDefault();
    setView('dashboard');
  };

  // Task Handlers
  const toggleComplete = (id) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t));
  };

  const deleteTask = (id) => {
    setTasks(tasks.filter(t => t.id !== id));
  };

  const saveTask = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const taskData = {
      id: editingTask ? editingTask.id : Date.now(),
      title: formData.get('title'),
      description: formData.get('description'),
      tags: formData.get('tags').split(',').map(s => s.trim()),
      dueDate: formData.get('dueDate'),
      status: formData.get('status') || 'pending',
    };

    if (editingTask) {
      setTasks(tasks.map(t => t.id === editingTask.id ? taskData : t));
    } else {
      setTasks([...tasks, taskData]);
    }
    setView('inventory');
    setEditingTask(null);
  };

  // Stats
  const stats = useMemo(() => ({
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    pending: tasks.filter(t => t.status === 'pending').length,
    dueToday: tasks.filter(t => t.dueDate === new Date().toISOString().split('T')[0]).length,
  }), [tasks]);

  const filteredTasks = tasks.filter(t => 
    t.title.toLowerCase().includes(search.toLowerCase()) || 
    t.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()))
  );

  // --- Views ---

  if (view === 'auth') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: tokens.colors.background, fontFamily: tokens.typography.fontSans }}>
        <Card style={{ width: '100%', maxWidth: '400px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🧩</div>
            <h1 style={{ fontSize: tokens.typography.sizeH1, fontWeight: tokens.typography.weightBold }}>{isLogin ? 'Welcome Back' : 'Join SWEAT'}</h1>
            <p style={{ color: tokens.colors.textMuted }}>Manage your tasks with precision.</p>
          </div>
          <form onSubmit={handleAuth}>
            <Input label="Email" type="email" placeholder="alex@example.com" required />
            <Input label="Password" type="password" placeholder="••••••••" required />
            <Button type="submit" style={{ width: '100%', marginBottom: '1rem' }}>{isLogin ? 'Sign In' : 'Create Account'}</Button>
          </form>
          <div style={{ textAlign: 'center' }}>
            <button 
              onClick={() => setIsLogin(!isLogin)} 
              style={{ background: 'none', border: 'none', color: tokens.colors.primary, cursor: 'pointer', fontSize: '0.875rem' }}
            >
              {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
            </button>
          </div>
        </Card>
      </div>
    );
  }

  const Layout = ({ children, title }) => (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: tokens.colors.background, fontFamily: tokens.typography.fontSans }}>
      {/* Sidebar */}
      <div style={{ width: '260px', backgroundColor: tokens.colors.surface, borderRight: `1px solid ${tokens.colors.border}`, padding: '2rem 1rem' }}>
        <div style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          🧩 SWEAT
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <Button variant={view === 'dashboard' ? 'primary' : 'outline'} onClick={() => setView('dashboard')} style={{ textAlign: 'left' }}>Dashboard</Button>
          <Button variant={view === 'inventory' ? 'primary' : 'outline'} onClick={() => setView('inventory')} style={{ textAlign: 'left' }}>Task Inventory</Button>
          <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: `1px solid ${tokens.colors.border}` }}>
            <div style={{ fontSize: '0.875rem', color: tokens.colors.textMuted, marginBottom: '1rem' }}>Logged in as <strong>Alex</strong></div>
            <Button variant="outline" onClick={() => setView('auth')} style={{ width: '100%', color: tokens.colors.danger }}>Logout</Button>
          </div>
        </nav>
      </div>
      {/* Content */}
      <div style={{ flex: 1, padding: tokens.spacing.containerPadding }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: tokens.typography.sizeH1, fontWeight: tokens.typography.weightBold }}>{title}</h1>
          <Button onClick={() => { setEditingTask(null); setView('editor'); }}>+ New Task</Button>
        </header>
        {children}
      </div>
    </div>
  );

  if (view === 'dashboard') {
    return (
      <Layout title="Dashboard">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: tokens.spacing.elementGap, marginBottom: '2rem' }}>
          <Card style={{ borderLeft: `4px solid ${tokens.colors.primary}` }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: '0.875rem' }}>Total Tasks</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.total}</div>
          </Card>
          <Card style={{ borderLeft: `4px solid ${tokens.colors.success}` }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: '0.875rem' }}>Completed</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.completed}</div>
          </Card>
          <Card style={{ borderLeft: `4px solid ${tokens.colors.warning}` }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: '0.875rem' }}>Pending</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.pending}</div>
          </Card>
          <Card style={{ borderLeft: `4px solid ${tokens.colors.danger}` }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: '0.875rem' }}>Due Today</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.dueToday}</div>
          </Card>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: tokens.spacing.elementGap }}>
          <Card>
            <h3 style={{ marginBottom: '1rem' }}>Recent Activity</h3>
            {tasks.slice(-3).reverse().map(t => (
              <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: `1px solid ${tokens.colors.border}` }}>
                <span>{t.title}</span>
                <span style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>{t.status}</span>
              </div>
            ))}
          </Card>
          <Card>
            <h3 style={{ marginBottom: '1rem' }}>Up Next</h3>
            <p style={{ color: tokens.colors.textMuted }}>Your schedule looks clear for the next few hours.</p>
          </Card>
        </div>
      </Layout>
    );
  }

  if (view === 'inventory') {
    return (
      <Layout title="Task Inventory">
        <div style={{ marginBottom: '1.5rem' }}>
          <Input 
            placeholder="Search tasks or tags..." 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredTasks.map(task => (
            <Card key={task.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: `4px solid ${task.status === 'completed' ? tokens.colors.success : tokens.colors.warning}` }}>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', textDecoration: task.status === 'completed' ? 'line-through' : 'none' }}>{task.title}</h4>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {task.tags.map(tag => (
                    <span key={tag} style={{ fontSize: '0.7rem', backgroundColor: tokens.colors.background, padding: '2px 8px', borderRadius: '12px', border: `1px solid ${tokens.colors.border}` }}>{tag}</span>
                  ))}
                  <span style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginLeft: '0.5rem' }}>📅 {task.dueDate}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button variant="outline" onClick={() => toggleComplete(task.id)} style={{ color: task.status === 'completed' ? tokens.colors.textMuted : tokens.colors.success }}>
                  {task.status === 'completed' ? 'Reopen' : 'Complete'}
                </Button>
                <Button variant="outline" onClick={() => { setEditingTask(task); setView('editor'); }}>Edit</Button>
                <Button variant="outline" onClick={() => deleteTask(task.id)} style={{ color: tokens.colors.danger }}>Delete</Button>
              </div>
            </Card>
          ))}
          {filteredTasks.length === 0 && <div style={{ textAlign: 'center', padding: '2rem', color: tokens.colors.textMuted }}>No tasks found.</div>}
        </div>
      </Layout>
    );
  }

  if (view === 'editor') {
    return (
      <Layout title={editingTask ? 'Edit Task' : 'Create Task'}>
        <Card style={{ maxWidth: '600px', margin: '0 auto' }}>
          <form onSubmit={saveTask}>
            <Input label="Task Title" name="title" defaultValue={editingTask?.title} placeholder="e.g. Finish quarterly report" required />
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: tokens.typography.weightMedium }}>Description</label>
              <textarea 
                name="description" 
                defaultValue={editingTask?.description}
                style={{ width: '100%', padding: '0.625rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}`, minHeight: '100px', fontFamily: 'inherit' }}
              />
            </div>
            <Input label="Tags (comma separated)" name="tags" defaultValue={editingTask?.tags?.join(', ')} placeholder="work, urgent, health" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Input label="Due Date" name="dueDate" type="date" defaultValue={editingTask?.dueDate || new Date().toISOString().split('T')[0]} />
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: tokens.typography.weightMedium }}>Status</label>
                <select name="status" defaultValue={editingTask?.status || 'pending'} style={{ width: '100%', padding: '0.625rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                  <option value="pending">Pending</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <Button type="submit" style={{ flex: 1 }}>{editingTask ? 'Update Task' : 'Save Task'}</Button>
              <Button type="button" variant="outline" onClick={() => setView('inventory')} style={{ flex: 1 }}>Cancel</Button>
            </div>
          </form>
        </Card>
      </Layout>
    );
  }

  return null;
}
