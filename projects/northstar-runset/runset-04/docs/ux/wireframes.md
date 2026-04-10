{
  "personas": [
    {
      "name": "Titan Lead",
      "role": "Project Manager",
      "goal": "Monitor team progress across multiple workstreams and filter by specific contributors to assess workload.",
      "pain_points": "Information overload and difficulty seeing who is working on what in real-time."
    },
    {
      "name": "Genesis Engineer",
      "role": "Developer",
      "goal": "Quickly update task status during standups and see their own assigned tasks without friction.",
      "pain_points": "Heavyweight project management tools that require multiple clicks to perform simple state changes."
    }
  ],
  "user_journey": [
    "User opens the Titan Genesis Task Board and sees the full board overview.",
    "User selects an assignee from the 'Filter by Assignee' dropdown to isolate specific tasks.",
    "User identifies a task in the 'To Do' column and drags it into the 'In Progress' column.",
    "The board automatically saves the new state to the backend database.",
    "User clears the filter to return to the global view."
  ],
  "screens": [
    {
      "name": "Main Dashboard",
      "description": "A single-page view containing the header and the kanban board.",
      "components": [
        "Header: Title 'Titan Genesis' and an Assignee Filter dropdown.",
        "Kanban Board: A horizontal layout with three fixed columns: To Do, In Progress, and Done.",
        "Task Card: Draggable elements containing Task Title, Assignee Name, and a priority indicator.",
        "Empty State: Visual cue when a column has no tasks or when filters return no results."
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#DAA520",
      "secondary": "#2F4F4F",
      "background": "#1A1A1D",
      "surface": "#2C2C2E",
      "text": "#E1E1E1",
      "accent": "#FFD700",
      "column_bg": "#121212"
    },
    "typography": {
      "font_family": "'Inter', 'Segoe UI', Roboto, sans-serif",
      "h1_size": "24px",
      "body_size": "14px",
      "card_title_size": "16px"
    },
    "spacing": {
      "padding_base": "16px",
      "gap_columns": "20px",
      "card_margin": "12px",
      "border_radius": "8px"
    },
    "shadows": {
      "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.3)",
      "drag_shadow": "0 10px 20px rgba(0, 0, 0, 0.5)"
    }
  }
}