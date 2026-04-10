# Product Spec (SDD)

{
  "name": "HabitTracker",
  "goal": "Build a single-file Python habit tracker with daily check-ins, streak tracking, and weekly progress visualization.",
  "constraints": [
    "Implementation must be contained within a single Python file.",
    "Data must persist between sessions (e.g., using a JSON file)."
  ],
  "acceptance_criteria": [
    "Users can create new habits with a unique name.",
    "Users can mark a habit as completed for the current day or a specific past date.",
    "System accurately calculates 'current streak' as the number of consecutive days of completion ending today or yesterday.",
    "System accurately calculates 'longest streak' as the historical maximum consecutive days of completion.",
    "System provides a weekly view showing completion status for the last 7 days.",
    "A dedicated function/hook `send_reminders()` exists for future integration with notification systems.",
    "The application can load and save its state to a local file (e.g., `habits.json`) to ensure data persistence."
  ]
}

> specify runner fallback: specify not found