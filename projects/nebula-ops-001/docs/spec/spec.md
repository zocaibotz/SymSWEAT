# Product Spec (SDD)

{
  "name": "NebulaOps",
  "acceptance_criteria": [
    "User can capture a raw idea with title and description in under 30 seconds",
    "User can score each idea on impact (1-10), effort (1-10), and urgency (1-10)",
    "Prioritization Engine calculates weighted score and sorts ideas descending Mission Board displays top 3 ideas by score as missions",
    "Weekly",
    "Each mission auto-generates at least 3 subtasks",
    "Progress Radar shows visual status indicators (Not Started, In Progress, Done, Blocked)",
    "User can mark tasks complete and add blockers with descriptions",
    "Progress Radar displays confidence trend line over past 4 weeks",
    "Reflection Loop generates retrospective with: what went well, what didn't, suggested next actions",
    "User can complete full workflow (add idea → prioritize → generate plan → track → reflect) in under 10 minutes",
    "Basic authentication restricts access to registered users only",
    "All core paths have automated unit/integration test coverage",
    "Application handles errors gracefully with user-friendly messages",
    "Application exposes health/ready endpoints for observability"
  ],
  "optional": {
    "goal": "AI-assisted personal launchpad helping solo founders convert chaotic ideas into weekly execution plans",
    "constraints": [
      "Production-minded MVP architecture",
      "Clean, testable modular code",
      "Basic auth (email/password or social)",
      "Clear acceptance criteria with test plan",
      "Observability hooks (logging, metrics endpoints)",
      "Robust error handling"
    ],
    "project_name": "NebulaOps"
  }
}

> specify runner fallback: specify not found