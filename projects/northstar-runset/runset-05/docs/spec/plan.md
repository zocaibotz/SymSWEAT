# Technical Plan (SDD)

## Goals
- Implement requirements from SDD spec

## Constraints
- Follow architecture + test-first process

## Requirement Snapshot
```json
{
  "name": "Personal Knowledge Base App",
  "goal": "Build a single-file Python application for managing personal knowledge using markdown notes, cross-linking (backlinks), and efficient search.",
  "acceptance_criteria": [
    "Users can create, edit, and delete notes in Markdown format.",
    "Notes automatically detect and display 'backlinks' (other notes that link to the current note).",
    "A quick search feature allows users to find notes by title or content keywords.",
    "Navigation between notes is possible via wiki-style links (e.g., [[Note Name]]).",
    "All note data is persisted to a local directory or file.",
    "The application runs as a single Python file without requiring complex external database setup."
  ],
  "constraints": {
    "architecture": "Single python file app",
    "language": "Python 3.x"
  }
}
```
