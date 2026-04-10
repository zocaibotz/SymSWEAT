{
  "personas": [
    {
      "name": "Alex the Achiever",
      "role": "Busy Professional",
      "goals": [
        "Maintain a 30-day meditation streak",
        "Quickly log daily water intake during meetings",
        "Visualize progress at the end of the week"
      ],
      "pain_points": [
        "Complex apps with too many notifications",
        "Losing progress data when switching devices",
        "Missing a day due to travel and needing to back-log"
      ]
    },
    {
      "name": "Jordan the Optimizer",
      "role": "Self-Improvement Enthusiast",
      "goals": [
        "Track multiple habits simultaneously (exercise, reading, coding)",
        "See data-driven longest streaks to stay motivated",
        "Integrate tracking into a terminal-based workflow"
      ],
      "pain_points": [
        "Lack of historical visibility",
        "Inaccurate streak calculations",
        "Hard-to-parse data files"
      ]
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Initialize Application",
      "description": "User runs the Python script; the app loads existing data from habits.json or creates a new state."
    },
    {
      "step": 2,
      "action": "Add New Habit",
      "description": "User enters a unique name (e.g., 'Morning Run') to start tracking a new goal."
    },
    {
      "step": 3,
      "action": "Daily Check-in",
      "description": "User marks 'Morning Run' as complete for today or enters a specific past ISO date."
    },
    {
      "step": 4,
      "action": "Review Progress",
      "description": "User views the dashboard to see current streaks, longest streaks, and the 7-day visualization grid."
    },
    {
      "step": 5,
      "action": "Exit & Save",
      "description": "The application automatically serializes the updated state to habits.json on close or after every action."
    }
  ],
  "screens": [
    {
      "id": "main_dashboard",
      "name": "Main Dashboard",
      "elements": [
        "Habit List Table",
        "Current Streak Badge",
        "Longest Streak Badge",
        "Weekly 7-Day Status Grid",
        "Action Menu (Add, Check-in, View Stats, Exit)"
      ]
    },
    {
      "id": "add_habit",
      "name": "Create Habit",
      "elements": [
        "Habit Name Input Field",
        "Validation Message (Unique Name Check)",
        "Confirmation Prompt"
      ]
    },
    {
      "id": "check_in",
      "name": "Mark Completion",
      "elements": [
        "Habit Selection Prompt",
        "Date Selection (Default: Today)",
        "Success Message with Updated Streak Count"
      ]
    },
    {
      "id": "weekly_visualization",
      "name": "Weekly Progress View",
      "elements": [
        "7-Day Header (Dates)",
        "Completion Row per Habit (Done: [X], Missed: [ ])",
        "Summary Statistics"
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#00FF00 (Success/Complete)",
      "secondary": "#FFA500 (Streak/Flame)",
      "background": "#000000 (Terminal Black)",
      "text": "#FFFFFF (High Contrast)",
      "error": "#FF0000 (Missed/Validation Error)",
      "neutral": "#808080 (Pending/Empty)"
    },
    "typography": {
      "font_family": "Monospace",
      "heading_style": "Bold Uppercase",
      "list_style": "ASCII Borders / Tables"
    },
    "symbols": {
      "completed": "\u2705",
      "missed": "\u274c",
      "streak_fire": "\ud83d\udd25",
      "pending": "\u25cb"
    },
    "layout": {
      "spacing": "2-line padding between menu sections",
      "border": "Box-drawing characters (\u250c \u2500 \u2510)"
    }
  }
}