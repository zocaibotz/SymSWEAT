import React, { useState, useMemo } from 'react';

// Titan Genesis CLI-inspired React Dashboard
export default function App() {
  const [screen, setScreen] = useState('DASHBOARD');
  const [expenses, setExpenses] = useState([
    { id: 1, date: '2026-02-28', category: 'Food', amount: 12.50, description: 'Coffee and Muffin' },
    { id: 2, date: '2026-02-27', category: 'Transport', amount: 5.00, description: 'Bus Fare' },
    { id: 3, date: '2026-02-26', category: 'Business', amount: 150.00, description: 'Domain Renewal' }
  ]);

  const [form, setForm] = useState({
    amount: '',
    category: 'Food',
    date: new Date().toISOString().split('T')[0],
    description: ''
  });

  const categories = ['Food', 'Transport', 'Business', 'Housing', 'Utilities', 'Custom'];

  const totalSpending = useMemo(() => 
    expenses.reduce((acc, curr) => acc + curr.amount, 0).toFixed(2)
  , [expenses]);

  const categoryBreakdown = useMemo(() => {
    const map = {};
    expenses.forEach(e => {
      map[e.category] = (map[e.category] || 0) + e.amount;
    });
    return Object.entries(map).map(([name, total]) => ({
      name,
      total,
      percentage: ((total / parseFloat(totalSpending)) * 100).toFixed(1)
    }));
  }, [expenses, totalSpending]);

  const handleAddExpense = (e) => {
    e.preventDefault();
    const newExpense = {
      id: expenses.length + 1,
      ...form,
      amount: parseFloat(form.amount) || 0
    };
    setExpenses([...expenses, newExpense]);
    setScreen('DASHBOARD');
    setForm({ amount: '', category: 'Food', date: new Date().toISOString().split('T')[0], description: '' });
  };

  const styles = {
    container: {
      backgroundColor: '#000',
      color: '#FFF',
      fontFamily: '"Courier New", Courier, monospace',
      minHeight: '100vh',
      padding: '20px',
      lineHeight: '1.4'
    },
    header: { color: '#00FF00', fontWeight: 'bold', whiteSpace: 'pre', marginBottom: '20px' },
    cyan: { color: '#00FFFF' },
    green: { color: '#00FF00' },
    yellow: { color: '#FFFF00' },
    red: { color: '#FF0000' },
    dim: { color: '#888', fontStyle: 'italic' },
    button: {
      background: 'none',
      border: '1px solid #00FFFF',
      color: '#00FFFF',
      padding: '5px 15px',
      marginRight: '10px',
      cursor: 'pointer',
      fontFamily: 'inherit'
    },
    input: {
      background: '#222',
      border: '1px solid #FFFF00',
      color: '#FFFF00',
      padding: '5px',
      marginBottom: '10px',
      width: '100%',
      maxWidth: '300px',
      display: 'block'
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      marginTop: '10px'
    },
    td: {
      border: '1px solid #444',
      padding: '8px',
      textAlign: 'left'
    }
  };

  const AsciiArt = () => (
    <div style={styles.header}>
{`████████╗██╗████████╗ █████╗ ███╗   ██╗
╚══██╔══╝██║╚══██╔══╝██╔══██╗████╗  ██║
   ██║   ██║   ██║   ███████║██╔██╗ ██║
   ██║   ██║   ██║   ██╔══██║██║╚██╗██║
   ██║   ██║   ██║   ██║  ██║██║ ╚████║
   ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝
   
  ██████╗ ███████╗███╗   ██╗███████╗███████╗██╗███████╗
 ██╔════╝ ██╔════╝████╗  ██║██╔════╝██╔════╝██║██╔════╝
 ██║  ███╗█████╗  ██╔██╗ ██║█████╗  ███████╗██║███████╗
 ██║   ██║██╔══╝  ██║╚██╗██║██╔══╝  ╚════██║██║╚════██║
 ╚██████╔╝███████╗██║ ╚████║███████╗███████║██║███████║
  ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝╚══════╝`}
    </div>
  );

  const Dashboard = () => (
    <div>
      <AsciiArt />
      <div style={{ margin: '20px 0' }}>
        <span style={styles.cyan}>[ SYSTEM STATUS ]: </span>
        <span style={styles.green}>ONLINE</span>
      </div>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ ...styles.cyan, fontWeight: 'bold' }}>CURRENT MONTH TOTAL SPENDING:</div>
        <div style={{ fontSize: '24px', color: '#00FF00' }}>$ {totalSpending}</div>
      </div>
      <div>
        <button style={styles.button} onClick={() => setScreen('ENTRY')}>[1] ADD EXPENSE</button>
        <button style={styles.button} onClick={() => setScreen('LIST')}>[2] LIST EXPENSES</button>
        <button style={styles.button} onClick={() => setScreen('SUMMARY')}>[3] MONTHLY SUMMARY</button>
        <button style={styles.button} onClick={() => alert('Data exported to expenses.csv (Mocked)')}>[4] EXPORT CSV</button>
      </div>
    </div>
  );

  const EntryForm = () => (
    <div>
      <h2 style={styles.cyan}>ADD NEW EXPENSE</h2>
      <form onSubmit={handleAddExpense}>
        <label style={styles.dim}>AMOUNT (USD):</label>
        <input 
          style={styles.input} 
          type="number" 
          step="0.01" 
          required 
          value={form.amount} 
          onChange={e => setForm({...form, amount: e.target.value})} 
        />
        
        <label style={styles.dim}>CATEGORY:</label>
        <select 
          style={styles.input} 
          value={form.category} 
          onChange={e => setForm({...form, category: e.target.value})}
        >
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <label style={styles.dim}>DATE (YYYY-MM-DD):</label>
        <input 
          style={styles.input} 
          type="date" 
          value={form.date} 
          onChange={e => setForm({...form, date: e.target.value})} 
        />

        <label style={styles.dim}>DESCRIPTION:</label>
        <input 
          style={styles.input} 
          type="text" 
          value={form.description} 
          onChange={e => setForm({...form, description: e.target.value})} 
        />

        <div style={{ marginTop: '20px' }}>
          <button type="submit" style={{ ...styles.button, borderColor: '#00FF00', color: '#00FF00' }}>SAVE ENTRY</button>
          <button type="button" style={styles.button} onClick={() => setScreen('DASHBOARD')}>CANCEL</button>
        </div>
      </form>
    </div>
  );

  const ExpenseList = () => (
    <div>
      <h2 style={styles.cyan}>TRANSACTION LOG</h2>
      <table style={styles.table}>
        <thead>
          <tr style={styles.cyan}>
            <th style={styles.td}>ID</th>
            <th style={styles.td}>DATE</th>
            <th style={styles.td}>CATEGORY</th>
            <th style={styles.td}>AMOUNT</th>
            <th style={styles.td}>DESCRIPTION</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map(e => (
            <tr key={e.id}>
              <td style={styles.td}>{e.id}</td>
              <td style={styles.td}>{e.date}</td>
              <td style={styles.td}>{e.category}</td>
              <td style={{ ...styles.td, color: '#00FF00' }}>${e.amount.toFixed(2)}</td>
              <td style={styles.td}>{e.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: '20px' }}>
        <button style={styles.button} onClick={() => setScreen('DASHBOARD')}>RETURN TO MENU</button>
      </div>
    </div>
  );

  const Summary = () => (
    <div>
      <h2 style={styles.cyan}>MONTHLY REPORTING - FEB 2026</h2>
      <div style={{ border: '1px solid #444', padding: '15px' }}>
        {categoryBreakdown.map(item => (
          <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
            <span>{item.name.toUpperCase()}</span>
            <span>
              <span style={styles.green}>${item.total.toFixed(2)}</span>
              <span style={{ marginLeft: '10px', ...styles.dim }}>({item.percentage}%)</span>
            </span>
          </div>
        ))}
        <div style={{ borderTop: '1px solid #444', marginTop: '10px', paddingTop: '10px', display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 'bold' }}>GRAND TOTAL</span>
          <span style={{ fontWeight: 'bold', color: '#00FF00' }}>${totalSpending}</span>
        </div>
      </div>
      <div style={{ marginTop: '20px' }}>
        <button style={styles.button} onClick={() => setScreen('DASHBOARD')}>RETURN TO MENU</button>
      </div>
    </div>
  );

  return (
    <div style={styles.container}>
      {screen === 'DASHBOARD' && <Dashboard />}
      {screen === 'ENTRY' && <EntryForm />}
      {screen === 'LIST' && <ExpenseList />}
      {screen === 'SUMMARY' && <Summary />}
    </div>
  );
}
