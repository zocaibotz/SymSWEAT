import React, { useState, useEffect } from 'react';

const COLORS = {
  primary: '#00FF00',
  secondary: '#FFA500',
  background: '#000000',
  text: '#FFFFFF',
  error: '#FF0000',
  neutral: '#808080',
};

const SYMBOLS = {
  completed: '✅',
  missed: '❌',
  streak_fire: '🔥',
  pending: '○',
};

export default function App() {
  const [habits, setHabits] = useState(() => {
    const saved = localStorage.getItem('habits');
    return saved ? JSON.parse(saved) : [];
  });
  const [view, setView] = useState('dashboard');
  const [newHabitName, setNewHabitName] = useState('');

  useEffect(() => {
    localStorage.setItem('habits', JSON.stringify(habits));
  }, [habits]);

  const addHabit = () => {
    if (!newHabitName.trim()) return;
    if (habits.find(h => h.name.toLowerCase() === newHabitName.toLowerCase())) {
      alert('Habit already exists!');
      return;
    }
    setHabits([...habits, { name: newHabitName, completedDates: [] }]);
    setNewHabitName('');
    setView('dashboard');
  };

  const toggleCheckIn = (habitName, dateStr) => {
    setHabits(prev => prev.map(h => {
      if (h.name === habitName) {
        const dates = h.completedDates.includes(dateStr)
          ? h.completedDates.filter(d => d !== dateStr)
          : [...h.completedDates, dateStr];
        return { ...h, completedDates: dates };
      }
      return h;
    }));
  };

  const calculateStreak = (completedDates) => {
    if (!completedDates.length) return { current: 0, longest: 0 };
    
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
    
    let current = 0;
    let d = completedDates.includes(today) ? new Date() : new Date(Date.now() - 86400000);
    
    if (completedDates.includes(today) || completedDates.includes(yesterday)) {
        while (completedDates.includes(d.toISOString().split('T')[0])) {
            current++;
            d.setDate(d.getDate() - 1);
        }
    }

    const allDates = [...new Set(completedDates)].sort();
    let longest = 0;
    let streak = 0;
    for (let i = 0; i < allDates.length; i++) {
        if (i > 0) {
            const prev = new Date(allDates[i-1]);
            const curr = new Date(allDates[i]);
            const diff = (curr - prev) / (1000 * 60 * 60 * 24);
            streak = (diff === 1) ? streak + 1 : 1;
        } else {
            streak = 1;
        }
        longest = Math.max(longest, streak);
    }

    return { current, longest };
  };

  const getLast7Days = () => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return d.toISOString().split('T')[0];
    });
  };

  const last7Days = getLast7Days();

  const styles = {
    container: {
      backgroundColor: COLORS.background,
      color: COLORS.text,
      fontFamily: 'monospace',
      minHeight: '100vh',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    },
    box: {
      border: '2px solid ' + COLORS.primary,
      padding: '20px',
      maxWidth: '800px',
      width: '100%',
      marginTop: '20px',
      backgroundColor: '#050505',
    },
    header: {
      textAlign: 'center',
      borderBottom: '1px solid ' + COLORS.primary,
      marginBottom: '20px', 
      paddingBottom: '10px',
      fontWeight: 'bold',
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      marginTop: '10px',
    },
    th: {
      borderBottom: '1px solid ' + COLORS.neutral,
      padding: '10px',
      textAlign: 'left',
      color: COLORS.primary,
    },
    td: {
      padding: '10px',
      borderBottom: '1px solid #222',
    },
    button: {
      backgroundColor: 'transparent',
      color: COLORS.primary,
      border: '1px solid ' + COLORS.primary,
      padding: '8px 16px',
      cursor: 'pointer',
      marginRight: '10px',
      fontFamily: 'monospace',
      textTransform: 'uppercase',
      fontWeight: 'bold',
    },
    input: {
      backgroundColor: '#111',
      color: COLORS.text,
      border: '1px solid ' + COLORS.primary,
      padding: '10px',
      width: 'calc(100% - 22px)',
      marginBottom: '10px',
      fontFamily: 'monospace',
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={{ color: COLORS.primary, letterSpacing: '4px' }}>┌──────────────────┐</h1>
      <h1 style={{ color: COLORS.primary, margin: '-10px 0' }}>│  S.W.E.A.T. APP  │</h1>
      <h1 style={{ color: COLORS.primary, letterSpacing: '4px' }}>└──────────────────┘</h1>
      
      {view === 'dashboard' && (
        <div style={styles.box}>
          <div style={styles.header}>
            DASHBOARD_MAIN_V1.0
          </div>
          <div style={{ marginBottom: '20px' }}>
            <button style={styles.button} onClick={() => setView('add')}>[+] NEW_HABIT</button>
            <button style={styles.button} onClick={() => setView('checkin')}>[✓] CHECK_IN</button>
          </div>

          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>HABIT_NAME</th>
                <th style={styles.th}>STREAK_INFO</th>
                <th style={styles.th}>WEEKLY_GRID</th>
              </tr>
            </thead>
            <tbody>
              {habits.map(habit => {
                const { current, longest } = calculateStreak(habit.completedDates);
                return (
                  <tr key={habit.name}>
                    <td style={styles.td}>{habit.name.toUpperCase()}</td>
                    <td style={styles.td}>
                      <span style={{ color: COLORS.secondary }}>{SYMBOLS.streak_fire} {current}</span>
                      <span style={{ color: COLORS.neutral, fontSize: '0.8em', marginLeft: '10px' }}>MAX:{longest}</span>
                    </td>
                    <td style={styles.td}>
                      {last7Days.map(date => (
                        <span key={date} title={date} style={{ margin: '0 3px', cursor: 'pointer' }} onClick={() => toggleCheckIn(habit.name, date)}>
                          {habit.completedDates.includes(date) ? SYMBOLS.completed : SYMBOLS.pending}
                        </span>
                      ))}
                    </td>
                  </tr>
                );
              })}
              {habits.length === 0 && (
                <tr>
                  <td colSpan="3" style={{ textAlign: 'center', padding: '40px', color: COLORS.neutral }}>NO DATA FOUND. RUN 'ADD_HABIT' TO INITIALIZE.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {view === 'add' && (
        <div style={styles.box}>
          <div style={styles.header}>INITIALIZE_NEW_HABIT</div>
          <p style={{ color: COLORS.neutral }}>INPUT UNIQUE IDENTIFIER:</p>
          <input 
            style={styles.input} 
            value={newHabitName} 
            onChange={(e) => setNewHabitName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addHabit()}
            placeholder="e.g. MORNING_MEDITATION"
            autoFocus
          />
          <div style={{ marginTop: '20px' }}>
            <button style={styles.button} onClick={addHabit}>EXECUTE</button>
            <button style={{ ...styles.button, borderColor: COLORS.error, color: COLORS.error }} onClick={() => setView('dashboard')}>ABORT</button>
          </div>
        </div>
      )}

      {view === 'checkin' && (
        <div style={styles.box}>
          <div style={styles.header}>MARK_COMPLETION_SEQ</div>
          <p style={{ color: COLORS.neutral }}>SELECT TARGET FOR {new Date().toISOString().split('T')[0]}:</p>
          <div style={{ display: 'grid', gap: '10px', marginTop: '10px' }}>
            {habits.map(habit => (
              <button 
                key={habit.name} 
                style={{ ...styles.button, textAlign: 'left', marginRight: 0 }}
                onClick={() => {
                  toggleCheckIn(habit.name, new Date().toISOString().split('T')[0]);
                  setView('dashboard');
                }}
              >
                [ ] {habit.name.toUpperCase()}
              </button>
            ))}
          </div>
          <button style={{ ...styles.button, marginTop: '20px', borderColor: COLORS.neutral, color: COLORS.neutral }} onClick={() => setView('dashboard')}>RETURN</button>
        </div>
      )}

      <div style={{ marginTop: '40px', color: COLORS.neutral, fontSize: '0.7em', textAlign: 'center', linePadding: '1.5' }}>
        <p>PERSONA_ACTIVE: ALEX_JORDAN | MODE: OPTIMIZATION_STRICT</p>
        <p>© 2026 S.W.E.A.T. TERMINAL INTERFACE</p>
      </div>
    </div>
  );
}
