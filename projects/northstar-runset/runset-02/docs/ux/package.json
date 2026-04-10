{
  "personas": [
    {
      "name": "Alex Miller",
      "role": "Budgeting Student",
      "pain_points": [
        "Loses track of small daily purchases",
        "Overwhelmed by complex accounting software",
        "Needs to know how much is left for the month at a glance"
      ],
      "goals": [
        "Quickly log a coffee or meal in under 10 seconds",
        "See a simple breakdown of food vs. transport costs"
      ]
    },
    {
      "name": "Jordan Casey",
      "role": "Freelance Consultant",
      "pain_points": [
        "Difficulty separating business expenses for tax season",
        "Prefers command-line tools over heavy GUI apps",
        "Manual data entry errors"
      ],
      "goals": [
        "Export clean CSV data for their accountant",
        "Categorize expenses strictly for reimbursement",
        "Ensure data is stored locally and privately"
      ]
    }
  ],
  "user_journey": [
    "User launches the 'Titan Genesis' CLI application",
    "Main menu displays current month's total spending and options",
    "User selects 'Add Expense' and enters amount, category, and description",
    "System validates input and confirms the entry is saved to local SQLite",
    "User selects 'Monthly Summary' to see a category-wise breakdown",
    "User selects 'Export' to generate an 'expenses.csv' file for external use",
    "User exits the application knowing their data is persisted"
  ],
  "screens": [
    {
      "name": "Main Dashboard",
      "elements": [
        "App Header (Ascii Art)",
        "Quick Summary (Current Month Total)",
        "Menu Options (Add, List, Summary, Export, Exit)"
      ],
      "layout": "Vertical list with bold headers"
    },
    {
      "name": "Expense Entry Form",
      "elements": [
        "Amount Prompt (float validation)",
        "Category Selection (Predefined list + Custom option)",
        "Date Input (Defaults to today)",
        "Description Field (Optional string)"
      ],
      "layout": "Sequential interactive prompts"
    },
    {
      "name": "Expense Table View",
      "elements": [
        "Tabular grid with columns: ID, Date, Category, Amount, Description",
        "Pagination or 'Press any key to continue' for long lists"
      ],
      "layout": "Grid-based ASCII table"
    },
    {
      "name": "Monthly Reporting",
      "elements": [
        "Month/Year Header",
        "Category Breakdown (Name, Total, Percentage)",
        "Grand Total for the period"
      ],
      "layout": "Grouped summary list"
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "Green (ANSI 32) - Success and Money",
      "secondary": "Cyan (ANSI 36) - Information and Headers",
      "warning": "Yellow (ANSI 33) - Inputs and Prompts",
      "error": "Red (ANSI 31) - Invalid Data/Crashes",
      "text": "White (ANSI 37) - Standard Output"
    },
    "typography": {
      "header": "Bold/Uppercase",
      "table_borders": "ASCII (Box Drawing Characters)",
      "prompts": "Italic/Dimmed"
    },
    "spacing": {
      "indent": "2 spaces",
      "vertical_margin": "1 newline between modules"
    }
  }
}