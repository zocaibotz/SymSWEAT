{
  "personas": [
    {
      "name": "The Solo Founder",
      "goal": "To maintain focus on product building while ensuring no operational tasks slip through the cracks.",
      "needs": [
        "Quick capture of daily tasks",
        "Clear visibility into overdue work",
        "Automated weekly recaps to pause and reflect"
      ]
    },
    {
      "name": "The Indie Ops Manager",
      "goal": "To manage small-scale incidents without a full NOC team, ensuring system health is trackable.",
      "needs": [
        "Incident logging with severity",
        "Historical log of issues",
        "Easy export for stakeholders"
      ]
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Onboarding",
      "description": "User registers and creates a secure, isolated workspace."
    },
    {
      "step": 2,
      "action": "Morning Check",
      "description": "User logs in to the Dashboard to view the 'pulse' of the week: open task count and active incidents grouped by severity."
    },
    {
      "step": 3,
      "action": "Task Execution",
      "description": "User creates new tasks for the week and updates statuses as they progress."
    },
    {
      "step": 4,
      "action": "Incident Response",
      "description": "User logs an incident (bug/outage), sets severity, and resolves it with notes."
    },
    {
      "step": 5,
      "action": "Weekly Close",
      "description": "User generates the Weekly Digest to review completed work and plan ahead."
    }
  ],
  "screens": [
    {
      "id": "auth_login",
      "components": [
        "Email Input",
        "Password Input",
        "Submit Button",
        "Link to Register"
      ]
    },
    {
      "id": "dashboard_home",
      "components": [
        "Stat Card: Open Tasks",
        "Stat Card: Critical Incidents",
        "Chart: Weekly Completion Trend",
        "Quick Action: Add Task"
      ]
    },
    {
      "id": "tasks_index",
      "components": [
        "Task List/Table",
        "Filters (Status, Due Date)",
        "Create Task Modal (Title, Status, Due Date)",
        "Edit/Delete Actions"
      ]
    },
    {
      "id": "incidents_index",
      "components": [
        "Incident List",
        "Severity Badges (Low/Med/High)",
        "Create Incident Modal (Title, Severity, Resolution Notes)"
      ]
    },
    {
      "id": "reports_export",
      "components": [
        "Export Button",
        "Preview Pane (Markdown rendered)"
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#FF4757",
      "secondary": "#2F3542",
      "background": "#F1F2F6",
      "surface": "#FFFFFF",
      "text_main": "#2F3542",
      "text_muted": "#747D8C",
      "success": "#2ED573",
      "danger": "#FF6B81"
    },
    "typography": {
      "font_family": "Inter, system-ui, sans-serif",
      "base_size": "16px",
      "heading_weight": "700"
    },
    "spacing": {
      "unit": "4px",
      "container_pad": "24px"
    },
    "effects": {
      "border_radius": "8px",
      "shadow_card": "0 4px 6px rgba(0,0,0,0.05)"
    }
  }
}