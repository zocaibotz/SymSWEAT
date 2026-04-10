# Product Spec (SDD)

{
  "project_name": "Titan Genesis",
  "name": "Simple Expense Tracker",
  "goal": "A single-file Python application to manage personal expenses with categorization, reporting, and data portability.",
  "constraints": [
    "Implementation must be contained within a single Python file.",
    "No external database servers (use SQLite or local JSON/CSV for persistence)."
  ],
  "acceptance_criteria": [
    "User can add an expense with amount, category, date, and an optional description.",
    "User can list all recorded expenses in a formatted table.",
    "The system provides a 'Monthly Summary' view that aggregates total spending per category for the current month.",
    "User can export all expense data to a 'expenses.csv' file.",
    "The application persists data between sessions using a local storage mechanism.",
    "The application handles invalid input (e.g., non-numeric amounts) without crashing."
  ]
}

> specify runner fallback: specify not found