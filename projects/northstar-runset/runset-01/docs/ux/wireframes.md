{
  "personas": [
    {
      "name": "Alex 'The Archivist' Chen",
      "role": "Project Researcher",
      "goal": "Capture complex research fragments and organize them using a robust tagging system for quick retrieval across multiple active projects.",
      "pain_points": "Information overload and the difficulty of finding specific insights within a growing volume of unorganized data."
    },
    {
      "name": "Sarah 'The Shield' Miller",
      "role": "Privacy Consultant",
      "goal": "Securely document sensitive strategy notes with the assurance that data is isolated and protected from unauthorized access.",
      "pain_points": "Concerns about data breaches and the lack of transparent security in mainstream note-taking apps."
    }
  ],
  "user_journey": [
    "Navigate to the Titan Genesis landing page and select 'Register'.",
    "Create a secure account with email and password.",
    "Log in to the application to access the personal dashboard.",
    "Create a new note with a title, content, and several descriptive tags.",
    "Receive immediate success feedback upon saving the note.",
    "Search for the note using a keyword found in its content.",
    "Filter the dashboard view by selecting one of the defined tags.",
    "Edit an existing note to update its content or tags.",
    "Delete a redundant note and confirm the action.",
    "Securely log out of the application."
  ],
  "screens": [
    {
      "name": "Authentication (Login/Register)",
      "components": [
        "Brand Logo (Titan Genesis)",
        "Switchable Auth Form (Email, Password fields)",
        "Call-to-Action Buttons (Login, Sign Up)",
        "Error/Success Message Banner"
      ],
      "actions": [
        "Register User",
        "Authenticate User",
        "Toggle View"
      ]
    },
    {
      "name": "Notes Dashboard",
      "components": [
        "Global Search Bar (Keywords)",
        "Tag Filtering Sidebar",
        "Note Grid/List View",
        "Floating 'New Note' Button",
        "User Profile/Logout Menu"
      ],
      "actions": [
        "Search Notes",
        "Filter by Tags",
        "Select Note for Detail View",
        "Initiate Logout"
      ]
    },
    {
      "name": "Note Editor",
      "components": [
        "Title Input Field",
        "Rich Text/Markdown Content Area",
        "Tag Input System (Chip-based)",
        "Action Bar (Save, Delete, Cancel)",
        "Last Edited Timestamp"
      ],
      "actions": [
        "Create Note",
        "Update Note",
        "Delete Note",
        "Return to Dashboard"
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#2C3E50",
      "secondary": "#E67E22",
      "background": "#F4F7F6",
      "surface": "#FFFFFF",
      "text_primary": "#2C3E50",
      "text_secondary": "#7F8C8D",
      "success": "#27AE60",
      "error": "#E74C3C",
      "accent": "#3498DB"
    },
    "typography": {
      "font_family": "'Inter', -apple-system, sans-serif",
      "h1": "2.25rem",
      "h2": "1.5rem",
      "body": "1rem",
      "caption": "0.875rem"
    },
    "spacing": {
      "base": "8px",
      "container_padding": "24px",
      "card_gap": "16px"
    },
    "ui_elements": {
      "border_radius": "6px",
      "shadow_soft": "0 2px 10px rgba(0,0,0,0.05)",
      "transition_speed": "0.2s ease"
    }
  }
}