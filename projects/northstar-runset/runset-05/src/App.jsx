import React, { useState, useMemo, useEffect } from 'react';

/**
 * Frontman 🧩 - Knowledge Workspace Implementation
 * Based on UX Package for Personal Knowledge Management
 */

const STYLE_TOKENS = {
  colors: {
    primary: '#3b82f6',
    background: '#f9fafb',
    surface: '#ffffff',
    text_main: '#111827',
    text_muted: '#6b7280',
    border: '#e5e7eb',
    accent: '#ef4444',
  },
  typography: {
    font_sans: 'Inter, system-ui, -apple-system, sans-serif',
    font_mono: "'JetBrains Mono', 'Fira Code', monospace",
    base_size: '16px',
    heading_weight: '600',
  },
  spacing: {
    container_padding: '2rem',
    element_gap: '1rem',
    border_radius: '0.5rem',
  },
  shadows: {
    card: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  },
};

export default function App() {
  const [notes, setNotes] = useState([
    {
      id: '1',
      title: 'Project X',
      content: '# Project X\n\nThis is the main hub for the project. Check [[Research Ideas]] for inspiration.',
      updatedAt: new Date().toISOString(),
    },
    {
      id: '2',
      title: 'Research Ideas',
      content: '# Research Ideas\n\n- Cognitive load in PKM tools\n- Link density analysis\n- Relates to [[Project X]]',
      updatedAt: new Date().toISOString(),
    },
  ]);

  const [activeNoteId, setActiveNoteId] = useState('1');
  const [searchQuery, setSearchQuery] = useState('');
  const [isPreview, setIsPreview] = useState(false);
  const [isSearchOverlayOpen, setIsSearchOverlayOpen] = useState(false);

  const activeNote = notes.find((n) => n.id === activeNoteId) || notes[0];

  // Helpers
  const createNewNote = (title = 'Untitled') => {
    const newNote = {
      id: Math.random().toString(36).substr(2, 9),
      title,
      content: `# ${title}\n\nStart writing...`,
      updatedAt: new Date().toISOString(),
    };
    setNotes([newNote, ...notes]);
    setActiveNoteId(newNote.id);
    setIsSearchOverlayOpen(false);
  };

  const updateNote = (id, updates) => {
    setNotes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, ...updates, updatedAt: new Date().toISOString() } : n))
    );
  };

  const deleteNote = (id) => {
    const remaining = notes.filter((n) => n.id !== id);
    setNotes(remaining);
    if (activeNoteId === id && remaining.length > 0) {
      setActiveNoteId(remaining[0].id);
    }
  };

  const backlinks = useMemo(() => {
    if (!activeNote) return [];
    return notes.filter(
      (n) => n.id !== activeNote.id && n.content.includes(`[[${activeNote.title}]]`)
    );
  }, [activeNote, notes]);

  const filteredNotes = notes.filter((n) =>
    n.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Simple Markdown Parser for Wiki-links
  const renderMarkdown = (text) => {
    const parts = text.split(/(\[\[.*?\]\])/g);
    return parts.map((part, i) => {
      if (part.startsWith('[[') && part.endsWith(']]')) {
        const title = part.slice(2, -2);
        const linkedNote = notes.find((n) => n.title.toLowerCase() === title.toLowerCase());
        return (
          <span
            key={i}
            style={{
              color: STYLE_TOKENS.colors.primary,
              cursor: 'pointer',
              textDecoration: 'underline',
              fontWeight: '500',
            }}
            onClick={() => {
              if (linkedNote) {
                setActiveNoteId(linkedNote.id);
              } else {
                createNewNote(title);
              }
            }}
          >
            {title}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="app-shell">
      <style>{`
        * { box-sizing: border-box; }
        body { 
          margin: 0; 
          font-family: ${STYLE_TOKENS.typography.font_sans}; 
          background-color: ${STYLE_TOKENS.colors.background}; 
          color: ${STYLE_TOKENS.colors.text_main};
          -webkit-font-smoothing: antialiased;
        }
        .app-shell { display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar {
          width: 300px;
          background: ${STYLE_TOKENS.colors.surface};
          border-right: 1px solid ${STYLE_TOKENS.colors.border};
          display: flex;
          flex-direction: column;
        }
        .sidebar-header {
          padding: 1.5rem 1rem;
          border-bottom: 1px solid ${STYLE_TOKENS.colors.border};
        }
        .search-input {
          width: 100%;
          padding: 0.6rem 0.8rem;
          border: 1px solid ${STYLE_TOKENS.colors.border};
          border-radius: ${STYLE_TOKENS.spacing.border_radius};
          font-size: 0.9rem;
          outline: none;
        }
        .search-input:focus { border-color: ${STYLE_TOKENS.colors.primary}; }
        .notes-list {
          flex: 1;
          overflow-y: auto;
          padding: 0.5rem;
        }
        .note-item {
          padding: 0.8rem 1rem;
          border-radius: ${STYLE_TOKENS.spacing.border_radius};
          cursor: pointer;
          margin-bottom: 0.2rem;
          transition: background 0.2s;
        }
        .note-item:hover { background: ${STYLE_TOKENS.colors.background}; }
        .note-item.active { 
          background: #eff6ff; 
          color: ${STYLE_TOKENS.colors.primary}; 
          font-weight: 500; 
        }
        .note-item-title { font-size: 0.95rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .note-item-date { font-size: 0.75rem; color: ${STYLE_TOKENS.colors.text_muted}; margin-top: 0.2rem; display: block; }

        /* Main Content */
        .main-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          background: ${STYLE_TOKENS.colors.surface};
        }
        .action-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1.5rem;
          border-bottom: 1px solid ${STYLE_TOKENS.colors.border};
        }
        .action-bar-left { display: flex; align-items: center; gap: 0.75rem; }
        .btn {
          padding: 0.5rem 1rem;
          border-radius: ${STYLE_TOKENS.spacing.border_radius};
          font-size: 0.875rem;
          cursor: pointer;
          border: 1px solid ${STYLE_TOKENS.colors.border};
          background: ${STYLE_TOKENS.colors.surface};
          color: ${STYLE_TOKENS.colors.text_main};
          font-weight: 500;
          transition: all 0.2s;
        }
        .btn:hover { background: ${STYLE_TOKENS.colors.background}; }
        .btn-primary {
          background: ${STYLE_TOKENS.colors.primary};
          color: white;
          border-color: ${STYLE_TOKENS.colors.primary};
        }
        .btn-primary:hover { opacity: 0.9; }
        .btn-danger { color: ${STYLE_TOKENS.colors.accent}; }
        .btn-danger:hover { background: #fee2e2; border-color: ${STYLE_TOKENS.colors.accent}; }

        .editor-container {
          flex: 1;
          display: flex;
          overflow: hidden;
        }
        .editor-textarea {
          flex: 1;
          padding: 2rem;
          border: none;
          resize: none;
          font-family: ${STYLE_TOKENS.typography.font_mono};
          font-size: 1rem;
          line-height: 1.6;
          outline: none;
          background: ${STYLE_TOKENS.colors.background};
        }
        .preview-area {
          flex: 1;
          padding: 2rem;
          overflow-y: auto;
          line-height: 1.6;
          white-space: pre-wrap;
        }
        .preview-area h1 { margin-top: 0; font-weight: ${STYLE_TOKENS.typography.heading_weight}; }

        /* Backlinks Panel */
        .backlinks-panel {
          width: 260px;
          border-left: 1px solid ${STYLE_TOKENS.colors.border};
          padding: 1.5rem;
          overflow-y: auto;
        }
        .backlinks-title {
          font-size: 0.8rem;
          font-weight: 700;
          text-transform: uppercase;
          color: ${STYLE_TOKENS.colors.text_muted};
          letter-spacing: 0.05em;
          margin-bottom: 1rem;
          display: block;
        }
        .backlink-item {
          font-size: 0.9rem;
          color: ${STYLE_TOKENS.colors.primary};
          margin-bottom: 0.75rem;
          cursor: pointer;
          display: block;
        }
        .backlink-item:hover { text-decoration: underline; }

        /* Search Overlay */
        .search-overlay {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.2);
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding-top: 15vh;
          z-index: 100;
        }
        .search-card {
          width: 600px;
          background: ${STYLE_TOKENS.colors.surface};
          border-radius: 0.75rem;
          box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
          overflow: hidden;
        }
        .search-card input {
          width: 100%;
          padding: 1.25rem;
          font-size: 1.1rem;
          border: none;
          border-bottom: 1px solid ${STYLE_TOKENS.colors.border};
          outline: none;
        }
        .search-results {
          max-height: 400px;
          overflow-y: auto;
          padding: 0.5rem;
        }
        .search-result-item {
          padding: 1rem;
          border-radius: 0.5rem;
          cursor: pointer;
        }
        .search-result-item:hover { background: ${STYLE_TOKENS.colors.background}; }
        .search-result-item.active { background: #eff6ff; }
        .search-result-meta { font-size: 0.8rem; color: ${STYLE_TOKENS.colors.text_muted}; margin-top: 0.25rem; }
      `}</style>

      <aside className="sidebar">
        <div className="sidebar-header">
          <input
            type="text"
            className="search-input"
            placeholder="Search or Create..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && searchQuery && filteredNotes.length === 0) {
                createNewNote(searchQuery);
                setSearchQuery('');
              }
            }}
          />
        </div>
        <div className="notes-list">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              className={`note-item ${note.id === activeNoteId ? 'active' : ''}`}
              onClick={() => setActiveNoteId(note.id)}
            >
              <span className="note-item-title">{note.title}</span>
              <span className="note-item-date">
                {new Date(note.updatedAt).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      </aside>

      <main className="main-content">
        <header className="action-bar">
          <div className="action-bar-left">
            <button className="btn" onClick={() => setIsPreview(!isPreview)}>
              {isPreview ? 'Edit' : 'Preview'}
            </button>
          </div>
          <div className="action-bar-right">
            <button className="btn" onClick={() => createNewNote()} style={{ marginRight: '0.5rem' }}>
              New Note
            </button>
            <button className="btn btn-danger" onClick={() => deleteNote(activeNoteId)}>
              Delete
            </button>
          </div>
        </header>

        <div className="editor-container">
          {isPreview ? (
            <div className="preview-area">{renderMarkdown(activeNote?.content || '')}</div>
          ) : (
            <textarea
              className="editor-textarea"
              value={activeNote?.content || ''}
              onChange={(e) => updateNote(activeNoteId, { content: e.target.value })}
              placeholder="Type your thoughts... use [[Link]] for wiki-links."
            />
          )}
        </div>
      </main>

      <aside className="backlinks-panel">
        <span className="backlinks-title">Backlinks</span>
        {backlinks.length > 0 ? (
          backlinks.map((note) => (
            <div
              key={note.id}
              className="backlink-item"
              onClick={() => setActiveNoteId(note.id)}
            >
              {note.title}
            </div>
          ))
        ) : (
          <div style={{ color: STYLE_TOKENS.colors.text_muted, fontSize: '0.85rem' }}>
            No notes link here yet.
          </div>
        )}
      </aside>

      {isSearchOverlayOpen && (
        <div className="search-overlay" onClick={() => setIsSearchOverlayOpen(false)}>
          <div className="search-card" onClick={(e) => e.stopPropagation()}>
            <input 
              autoFocus 
              placeholder="Type to search everything..." 
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <div className="search-results">
              {filteredNotes.map((note) => (
                <div
                  key={note.id}
                  className="search-result-item"
                  onClick={() => {
                    setActiveNoteId(note.id);
                    setIsSearchOverlayOpen(false);
                  }}
                >
                  <div style={{ fontWeight: '600' }}>{note.title}</div>
                  <div className="search-result-meta">
                    {note.content.substring(0, 80)}...
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
