# TODO API Specification

## 1. Project Overview

- **Project Name**: TODO API
- **Project Type**: REST API
- **Core Functionality**: A minimal TODO list API that allows adding, listing, and completing tasks
- **Target Users**: Developers needing a simple TODO backend

## 2. Functionality Specification

### Core Features

- **Add Task**: Create a new todo item with a description
- **List Tasks**: Retrieve all todo items (both active and completed)
- **Complete Task**: Mark a todo item as done

### Data Model

```
todo:
  - id: integer (auto-increment)
  - description: string (required)
  - completed: boolean (default: false)
  - created_at: datetime
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /todos | Add a new todo |
| GET | /todos | List all todos |
| PATCH | /todos/{id}/complete | Mark a todo as complete |

### Request/Response Formats

#### POST /todos
- Request: `{"description": "Buy milk"}`
- Response: `{"id": 1, "description": "Buy milk", "completed": false}`

#### GET /todos
- Response: `[{"id": 1, "description": "Buy milk", "completed": false}]`

#### PATCH /todos/{id}/complete
- Response: `{"id": 1, "description": "Buy milk", "completed": true}`

## 3. Acceptance Criteria

- [ ] Can add a new todo with a description
- [ ] Can list all todos
- [ ] Can mark a todo as complete
- [ ] Returns proper HTTP status codes
- [ ] Handles missing resources gracefully (404)
- [ ] Validates required fields
