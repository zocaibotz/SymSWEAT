import React, { useState } from 'react';

const INITIAL_TASKS = [
  { id: 1, title: 'Initialize Titan Project', assignee: 'Titan Lead', status: 'Done', priority: 'High' },
  { id: 2, title: 'Design System Architecture', assignee: 'Titan Lead', status: 'In Progress', priority: 'Critical' },
  { id: 3, title: 'Implement Kanban UI', assignee: 'Genesis Engineer', status: 'In Progress', priority: 'High' },
  { id: 4, title: 'Setup Backend Database', assignee: 'Genesis Engineer', status: 'To Do', priority: 'Medium' },
  { id: 5, title: 'Write Unit Tests', assignee: 'Genesis Engineer', status: 'To Do', priority: 'Low' },
];

export default function App() {
  const [tasks, setTasks] = useState(INITIAL_TASKS);
  const [filter, setFilter] = useState('All');

  const assignees = ['All', ...new Set(INITIAL_TASKS.map(t => t.assignee))];
  const columns = ['To Do', 'In Progress', 'Done'];

  const onDragStart = (e, taskId) => {
    e.dataTransfer.setData('taskId', taskId);
  };

  const onDragOver = (e) => {
    e.preventDefault();
  };

  const onDrop = (e, newStatus) => {
    const taskId = e.dataTransfer.getData('taskId');
    const updatedTasks = tasks.map(task => {
      if (task.id.toString() === taskId) {
        return { ...task, status: newStatus };
      }
      return task;
    });
    setTasks(updatedTasks);
    // Log simulated backend sync
    console.log(`State synced: Task ${taskId} moved to ${newStatus}`);
  };

  const filteredTasks = filter === 'All' ? tasks : tasks.filter(t => t.assignee === filter);

  return (
    <div className="app-container">
      <style>{`
        :root {
          --primary: #DAA520;
          --secondary: #2F4F4F;
          --background: #1A1A1D;
          --surface: #2C2C2E;
          --text: #E1E1E1;
          --accent: #FFD700;
          --column-bg: #121212;
          --padding: 16px;
          --gap: 20px;
          --radius: 8px;
          --shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
          --drag-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
        }

        body {
          margin: 0;
          background-color: var(--background);
          color: var(--text);
          font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
          -webkit-font-smoothing: antialiased;
        }

        .app-container {
          padding: calc(var(--padding) * 2);
          max-width: 1400px;
          margin: 0 auto;
          min-height: 100vh;
        }

        header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 40px;
          padding-bottom: 20px;
          border-bottom: 1px solid var(--secondary);
        }

        h1 {
          color: var(--primary);
          font-size: 28px;
          margin: 0;
          letter-spacing: 1px;
          text-transform: uppercase;
        }

        .filter-section {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .filter-section label {
          font-size: 14px;
          font-weight: 500;
          color: var(--accent);
        }

        select {
          background: var(--surface);
          color: var(--text);
          border: 1px solid var(--secondary);
          padding: 10px 16px;
          border-radius: var(--radius);
          outline: none;
          cursor: pointer;
          font-size: 14px;
          transition: border-color 0.2s;
        }

        select:focus {
          border-color: var(--primary);
        }

        .board {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--gap);
          align-items: start;
        }

        .column {
          background: var(--column-bg);
          border-radius: var(--radius);
          padding: var(--padding);
          min-height: 600px;
          display: flex;
          flex-direction: column;
          gap: var(--padding);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .column-header {
          font-weight: 700;
          font-size: 14px;
          text-transform: uppercase;
          color: var(--primary);
          display: flex;
          justify-content: space-between;
          padding: 0 4px;
        }

        .task-card {
          background: var(--surface);
          padding: 20px;
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          cursor: grab;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          border-left: 4px solid var(--secondary);
        }

        .task-card:hover {
          transform: translateY(-2px);
          box-shadow: var(--drag-shadow);
          border-left-color: var(--primary);
        }

        .task-card:active {
          cursor: grabbing;
        }

        .task-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 16px;
          line-height: 1.4;
        }

        .task-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 12px;
        }

        .assignee {
          display: flex;
          align-items: center;
          gap: 6px;
          opacity: 0.8;
        }

        .priority-tag {
          background: var(--secondary);
          color: var(--accent);
          padding: 4px 8px;
          border-radius: 4px;
          font-weight: 800;
          font-size: 10px;
          text-transform: uppercase;
        }

        .empty-state {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px dashed rgba(255, 255, 255, 0.05);
          border-radius: var(--radius);
          color: rgba(225, 225, 225, 0.3);
          font-size: 14px;
          font-style: italic;
          margin-top: 10px;
        }
      `}</style>

      <header>
        <h1>Titan Genesis</h1>
        <div className="filter-section">
          <label>Filter by Assignee</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            {assignees.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>
      </header>

      <main className="board">
        {columns.map(status => {
          const columnTasks = filteredTasks.filter(t => t.status === status);
          return (
            <div 
              key={status} 
              className="column"
              onDragOver={onDragOver}
              onDrop={(e) => onDrop(e, status)}
            >
              <div className="column-header">
                <span>{status}</span>
                <span style={{opacity: 0.5}}>{columnTasks.length}</span>
              </div>
              
              {columnTasks.length === 0 ? (
                <div className="empty-state">No tasks available</div>
              ) : (
                columnTasks.map(task => (
                  <div 
                    key={task.id} 
                    className="task-card" 
                    draggable 
                    onDragStart={(e) => onDragStart(e, task.id)}
                  >
                    <div className="task-title">{task.title}</div>
                    <div className="task-footer">
                      <div className="assignee">
                        <span>👤</span>
                        <span>{task.assignee}</span>
                      </div>
                      <div className="priority-tag">{task.priority}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </main>
    </div>
  );
}
