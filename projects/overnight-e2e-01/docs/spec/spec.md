# Product Spec (SDD)

{
  "name": "TaskMaster MVP",
  "project_name": "task-master-mvp",
  "goal": "Deliver a production-ready, single-file task management application featuring authentication, full CRUD capabilities, and a status dashboard.",
  "constraints": [
    "Architecture: Single Python file (e.g., FastAPI with Jinja2 or Flask)",
    "Database: SQLite for local persistence",
    "Security: Secure password hashing (bcrypt) and session-based or JWT authentication",
    "UI: Embedded HTML/CSS templates for a responsive dashboard and task views",
    "Deployment: Must be executable with a single 'python app.py' command"
  ],
  "acceptance_criteria": [
    "User can register a new account and log in securely.",
    "User can only access, edit, or delete tasks they have created (multi-tenancy).",
    "User can create a task with a title, description, tags, and a due date.",
    "User can view a list of their tasks with status indicators (Pending/Completed).",
    "User can update any task field, including marking tasks as complete.",
    "User can permanently delete a task.",
    "Dashboard displays real-time counts for 'Total Tasks', 'Completed', 'Pending', and 'Due Today'.",
    "Application handles errors gracefully (e.g., 404 for missing tasks, 401 for unauthorized access).",
    "All backend logic, database schema definitions, and frontend UI code reside in one Python file."
  ]
}

> specify runner fallback: specify not found