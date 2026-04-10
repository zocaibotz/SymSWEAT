# ZOC-91 Spec: Backend API for Decisions & Problems

## Context
The project tracker needs a backend API that captures AI/project **decisions** and operational **problems** and provides a merged timeline for UX surfaces.

## Goals
1. Create REST endpoints for decisions and problems.
2. Validate request payloads to prevent malformed records.
3. Provide a project-scoped timeline endpoint that merges decision/problem events in time order.
4. Keep implementation small and testable for targeted remediation.

## Scope
- In-memory repository (no database migration in this ticket).
- Express API only.
- Automated tests covering validation and happy paths.

## API Contract (Ticket Scope)

### POST `/api/decisions`
Create a decision item.

Required fields:
- `projectId` (string)
- `title` (string)
- `rationale` (string)

Optional fields:
- `alternatives` (array of strings)
- `decidedBy` (string)

Response: `201` with created record.

### GET `/api/decisions/:id`
Fetch decision by id.

Response: `200` record or `404`.

### POST `/api/problems`
Create a problem item.

Required fields:
- `projectId` (string)
- `summary` (string)
- `severity` (`low|medium|high|critical`)

Optional fields:
- `status` (`open|investigating|resolved`, default `open`)

Response: `201` with created record.

### PATCH `/api/problems/:id`
Update an existing problem.

Allowed fields:
- `status`
- `resolution`

Response: `200` updated record or `404`.

### GET `/api/projects/:projectId/timeline`
Merged chronological list of decisions/problems for one project.

Response shape:
```json
{
  "projectId": "proj-1",
  "events": [
    {"type":"decision", ...},
    {"type":"problem", ...}
  ]
}
```

## Non-Goals
- Persistence layer.
- Authentication/authorization.
- Multi-tenant isolation beyond projectId filtering.

## Risks and Mitigations
- **Risk:** malformed payloads break downstream timeline rendering.
  - **Mitigation:** strict lightweight input validation + tests.
- **Risk:** high/critical problem records not distinguishable.
  - **Mitigation:** explicit severity enum and enforced validation.

## Acceptance Criteria
- All endpoints above are implemented.
- Invalid payloads return `400` with stable error format.
- Timeline merges decision/problem events sorted by `createdAt`.
- Tests show red->green progression in run logs.
- Security scan report exists at `reports/security_scan.txt` with no unresolved high/critical findings.
als
- Database integration.
- Authn/authz.
- Pagination.

## Test Plan (TDD)
- Red phase: API tests for all 4 endpoints and filtering/search behavior.
- Green phase: implement Express app/service to satisfy tests.
- Verify structured logs include `level`, `type`, `phase`, and linkage ids.

## Security Considerations
- No dynamic code execution.
- Input validation to avoid malformed payloads.
- `npm audit` gate; remediate high/critical vulnerabilities.
