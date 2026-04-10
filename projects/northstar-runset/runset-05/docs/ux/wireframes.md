{
  "personas": [
    {
      "id": "researcher_alex",
      "name": "Alex the Researcher",
      "goal": "To build a dense web of interconnected ideas for a long-form writing project without the friction of a complex database.",
      "pain_points": [
        "Losing track of how ideas relate over time",
        "Overhead of managing multiple files or complex folders"
      ]
    },
    {
      "id": "student_sam",
      "name": "Sam the Student",
      "goal": "Quickly capture lecture snippets and find them later using keywords or related topics.",
      "pain_points": [
        "Slow search in traditional note apps",
        "No easy way to see what other notes mention the current topic"
      ]
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Search or Create",
      "description": "User enters a term in the quick search. If it doesn't exist, they hit 'Create New'."
    },
    {
      "step": 2,
      "action": "Drafting with Wiki-links",
      "description": "User writes markdown and types [[Project X]] to link to a related note."
    },
    {
      "step": 3,
      "action": "Discovery via Backlinks",
      "description": "User opens 'Project X' and scrolls down to see the 'Backlinks' section, discovering the note they just wrote."
    },
    {
      "step": 4,
      "action": "Navigation",
      "description": "User clicks a backlink to jump back to a previous context, maintaining flow."
    }
  ],
  "screens": [
    {
      "id": "main_dashboard",
      "name": "Knowledge Workspace",
      "components": [
        "Sidebar with Search Bar and Recent Notes list",
        "Markdown Editor with syntax highlighting",
        "Live Markdown Preview toggle",
        "Backlinks Panel showing a list of notes linking to the active note",
        "Action Bar: Save, Delete, New Note"
      ]
    },
    {
      "id": "search_overlay",
      "name": "Global Quick Search",
      "components": [
        "Omni-search input field",
        "Real-time result list with Title and Content snippets",
        "Keyboard navigation (Up/Down/Enter)"
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#3b82f6",
      "background": "#f9fafb",
      "surface": "#ffffff",
      "text_main": "#111827",
      "text_muted": "#6b7280",
      "border": "#e5e7eb",
      "accent": "#ef4444"
    },
    "typography": {
      "font_sans": "Inter, system-ui, sans-serif",
      "font_mono": "'JetBrains Mono', monospace",
      "base_size": "16px",
      "heading_weight": "600"
    },
    "spacing": {
      "container_padding": "2rem",
      "element_gap": "1rem",
      "border_radius": "0.5rem"
    },
    "shadows": {
      "card": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)"
    }
  }
}