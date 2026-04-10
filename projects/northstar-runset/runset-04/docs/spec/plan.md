# Technical Plan (SDD)

## Goals
- Implement requirements from SDD spec

## Constraints
- Follow architecture + test-first process

## Requirement Snapshot
```json
{
  "name": "Titan Genesis Task Board",
  "goal": "Create a lightweight, single-file Python task board with drag-and-drop status management and assignee filtering.",
  "acceptance_criteria": [
    "The application displays multiple columns representing task states (e.g., To Do, In Progress, Done).",
    "Users can drag and drop task cards between columns to update their status.",
    "Users can filter the displayed tasks by assignee name.",
    "The application is contained within a single Python file using a lightweight web framework (e.g., Flask or FastAPI).",
    "Task state is persisted (e.g., to a local JSON file or SQLite database)."
  ],
  "constraints": [
    "Architecture: Single python file app",
    "Target Platform: Linux"
  ]
}
```
