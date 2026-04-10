# Product Spec (SDD)

{
  "name": "Titan Genesis",
  "project_name": "Titan Genesis Note-Taking MVP",
  "goal": "Develop a functional MVP for a note-taking application that allows users to securely manage their notes with organizational features like search and tagging.",
  "acceptance_criteria": [
    "Users can register a new account and securely log in and log out.",
    "Authenticated users can create notes with a title, content, and tags.",
    "Authenticated users can retrieve, update, and delete only their own notes.",
    "Users can search for specific notes using keywords found in the title or content.",
    "Users can filter the list of notes by one or more tags.",
    "The application prevents unauthorized access to any note data by non-owners.",
    "The system provides clear feedback (success/error messages) for all CRUD operations and authentication attempts."
  ],
  "constraints": [
    "The application must be implemented using Python.",
    "Must support multiple concurrent users with data isolation."
  ]
}

> specify runner fallback: specify not found