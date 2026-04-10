{
  "personas": [
    {
      "name": "Alex the Architect",
      "role": "Tech Lead",
      "goal": "Monitor progress of multiple SWEAT projects and quickly jump into specific artefacts (Specs, Linear Issues) to unblock the team.",
      "pain_points": "Slow loading pages, difficulty finding specific documentation, lack of visibility into current flow stages."
    },
    {
      "name": "Sam the Manager",
      "role": "Project Manager",
      "goal": "Get a high-level overview of 'Titan Genesis' status, check completion percentages, and verify real-time task stats.",
      "pain_points": "Switching between multiple tools (Linear, Jira, GitHub) to get a full picture."
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Login to Command Center",
      "system_response": "Loads Dashboard view instantly (<2s)."
    },
    {
      "step": 2,
      "action": "Scan Project List",
      "system_response": "User sees 'Titan Genesis' in the list with a 'In-Progress' status and '65%' completion bar."
    },
    {
      "step": 3,
      "action": "Click Project Card",
      "system_response": "Navigates to Detail Page."
    },
    {
      "step": 4,
      "action": "Analyze Flow",
      "system_response": "Top flow indicator shows 'Architecture Blueprint' as active (highlighted), previous stages green, future stages gray."
    },
    {
      "step": 5,
      "action": "Review Stats & Artefacts",
      "system_response": "Checks right sidebar for Linear issue counts. Clicks 'Specification Doc' link in the artefacts section to open in new tab."
    }
  ],
  "screens": [
    {
      "name": "Dashboard View (Titan Genesis)",
      "layout": "Grid Layout (1920x1080 optimized)",
      "header": {
        "left": "SWEAT Command Center",
        "right": "User Avatar, Dark Mode Toggle, Global Search"
      },
      "components": [
        {
          "type": "Project Card",
          "content": [
            "Project Name: Titan Genesis",
            "Status Badge: In-Progress (Blue)",
            "Flow Stage: Architecture Blueprint",
            "Last Updated: 10 mins ago",
            "Progress Bar: 65% (Visual filled bar)"
          ],
          "interaction": "Hover effect: Elevate card + shadow. Click: Navigate to /project/titan-genesis"
        }
      ]
    },
    {
      "name": "Project Detail View",
      "layout": "3-Column Layout (Left: Flow/Nav, Center: Details, Right: Stats)",
      "sections": [
        {
          "section": "Top Bar",
          "content": "Breadcrumbs: Dashboard > Titan Genesis"
        },
        {
          "section": "Flow Indicator (Top Center)",
          "type": "Horizontal Stepper",
          "stages": [
            "Requirement Master",
            "Spec Forge",
            "Architecture Blueprint",
            "Plan Craft",
            "Code Smith"
          ],
          "state_logic": "Current stage 'Architecture Blueprint' highlighted with Primary Color border/bg. Previous stages marked 'Completed' with checkmark icon."
        },
        {
          "section": "Main Content (Center)",
          "content": "Detailed information about the current active stage (Architecture Blueprint). Includes active tasks, owner, and brief description."
        },
        {
          "section": "Right Sidebar (Stats)",
          "type": "Data Grid",
          "widgets": [
            "Total Tasks: 42",
            "Completed: 28",
            "In-Progress: 8",
            "Linear: Open (4) / Closed (30)"
          ]
        },
        {
          "section": "Artefacts Panel (Bottom or Tab)",
          "layout": "Categorized List",
          "categories": [
            {
              "name": "Documentation",
              "items": [
                "Requirements.pdf",
                "Spec_v2.docx"
              ]
            },
            {
              "name": "Project Management",
              "items": [
                "Sprint Plan",
                "Linear Issues (Link)"
              ]
            }
          ],
          "interaction": "Icons for file types. Hover shows 'Open in new tab'."
        }
      ]
    }
  ],
  "style_tokens": {
    "theme": "Command Center Dark",
    "colors": {
      "background_main": "#0f172a",
      "background_card": "#1e293b",
      "background_sidebar": "#111827",
      "text_primary": "#f8fafc",
      "text_secondary": "#94a3b8",
      "accent_primary": "#3b82f6",
      "accent_success": "#10b981",
      "accent_warning": "#f59e0b",
      "accent_danger": "#ef4444",
      "border": "#334155"
    },
    "typography": {
      "font_family_heading": "Inter, sans-serif",
      "font_family_body": "Roboto, sans-serif",
      "font_family_mono": "JetBrains Mono, monospace",
      "sizes": {
        "h1": "24px",
        "h2": "20px",
        "body": "14px",
        "caption": "12px"
      }
    },
    "spacing": {
      "unit": "4px",
      "card_padding": "24px",
      "grid_gap": "16px"
    },
    "effects": {
      "card_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.5)",
      "hover_transition": "all 0.2s ease-in-out"
    }
  }
}