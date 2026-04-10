{
  "personas": [
    {
      "name": "The Solo Builder",
      "role": "Founder/Developer/Operator",
      "needs": "A single source of truth for operational tasks and incidents without the overhead of enterprise tools. Needs to switch quickly between coding and operations.",
      "pain_points": "Losing track of small tasks, forgetting incident resolutions, lack of weekly progress visibility.",
      "goals": "Close weekly priorities, ensure operational stability, export summaries for personal review or sharing."
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Onboarding & Authentication",
      "description": "User registers a new account and logs in. System isolates data to this user."
    },
    {
      "step": 2,
      "action": "Dashboard Review",
      "description": "User lands on the main dashboard to see high-level KPIs: Open Tasks, Incidents by Severity, and Weekly Completion trends."
    },
    {
      "step": 3,
      "action": "Task Management",
      "description": "User creates tasks with due dates and status. They update or delete tasks as work progresses."
    },
    {
      "step": 4,
      "action": "Incident Logging",
      "description": "If an issue arises, the user logs an incident, assigns severity, and adds resolution notes once solved."
    },
    {
      "step": 5,
      "action": "Weekly Digest",
      "description": "At the end of the week, the user triggers the Markdown Export to review completed tasks, open risks, and incidents."
    },
    {
      "step": 6,
      "action": "Logout",
      "description": "User logs out to ensure data security."
    }
  ],
  "screens": [
    {
      "screen_id": "auth_screen",
      "name": "Authentication",
      "type": "Form",
      "elements": [
        "Email Input",
        "Password Input",
        "Register Toggle/Link",
        "Login Button",
        "Logout Button (Header)"
      ],
      "functionality": "Handles registration and login logic. Persists session via secure cookie or token."
    },
    {
      "screen_id": "dashboard_screen",
      "name": "Operations Dashboard",
      "type": "Home",
      "elements": [
        "Summary Cards (Open Tasks Count, Critical Incidents)",
        "Severity Distribution Chart (Pie/Bar)",
        "Weekly Completion Trend (Line Chart)",
        "Quick Action Buttons (New Task, Log Incident)"
      ],
      "functionality": "Aggregates data from SQLite to provide immediate operational visibility."
    },
    {
      "screen_id": "task_list_screen",
      "name": "Task Manager",
      "type": "List View",
      "elements": [
        "Task Table/List",
        "Status Badges (Todo, In Progress, Done)",
        "Due Date Display",
        "Add Task Button",
        "Edit/Delete Actions per Row"
      ],
      "functionality": "CRUD operations for tasks. Filters by status."
    },
    {
      "screen_id": "task_form_screen",
      "name": "Task Editor",
      "type": "Modal/Page",
      "elements": [
        "Title Input",
        "Description Textarea",
        "Status Dropdown",
        "Due Date Picker",
        "Save Button",
        "Cancel Button"
      ]
    },
    {
      "screen_id": "incident_list_screen",
      "name": "Incident Log",
      "type": "List View",
      "elements": [
        "Incident Table",
        "Severity Indicators (High/Medium/Low - Color Coded)",
        "Resolution Status (Open/Resolved)",
        "Add Incident Button"
      ],
      "functionality": "CRUD for incidents. Visual emphasis on severity."
    },
    {
      "screen_id": "incident_form_screen",
      "name": "Incident Editor",
      "type": "Modal/Page",
      "elements": [
        "Title Input",
        "Severity Dropdown (Critical, High, Medium, Low)",
        "Resolution Notes Textarea",
        "Save Button"
      ]
    },
    {
      "screen_id": "digest_screen",
      "name": "Weekly Digest Export",
      "type": "Report",
      "elements": [
        "Date Range Selector (Default: Last 7 Days)",
        "Preview Area (Markdown Render)",
        "Download Markdown Button"
      ],
      "functionality": "Generates a markdown file summarizing completed tasks, open risks (unresolved incidents), and incident recap."
    }
  ],
  "style_tokens": {
    "color_palette": {
      "primary": "#3B82F6",
      "primary_hover": "#2563EB",
      "secondary": "#64748B",
      "success": "#10B981",
      "warning": "#F59E0B",
      "danger": "#EF4444",
      "background": "#F8FAFC",
      "surface": "#FFFFFF",
      "text_main": "#1E293B",
      "text_muted": "#64748B"
    },
    "typography": {
      "font_family": "Inter, system-ui, -apple-system, sans-serif",
      "heading_weight": "700",
      "body_weight": "400",
      "base_size": "16px"
    },
    "spacing": {
      "container_padding": "2rem",
      "card_padding": "1.5rem",
      "element_gap": "1rem"
    },
    "visual_effects": {
      "border_radius": "8px",
      "shadow_card": "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
      "transition": "all 0.2s ease-in-out"
    },
    "layout": {
      "type": "Single Column Dashboard with Sidebar Navigation",
      "max_width": "1200px"
    }
  }
}