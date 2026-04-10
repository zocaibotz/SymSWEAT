{
  "personas": [
    {
      "name": "Diabetic Patient",
      "goals": "Easily monitor sugar and calorie intake to manage blood glucose levels without manual logging.",
      "frustrations": "Manual calorie counting is tedious; fear of hidden sugars in meals."
    },
    {
      "name": "Health Enthusiast",
      "goals": "Quickly track nutritional data of meals using visual recognition to maintain a balanced diet.",
      "frustrations": "Complex logging processes; lack of immediate feedback on meal composition."
    }
  ],
  "user_journey": [
    {
      "step": 1,
      "action": "Open Application",
      "description": "User launches the app and views the Dashboard displaying daily calorie/sugar totals and recent logs."
    },
    {
      "step": 2,
      "action": "Initiate Photo Upload",
      "description": "User taps 'Add Food' and selects an image from the gallery or takes a new photo of their meal."
    },
    {
      "step": 3,
      "action": "AI Analysis",
      "description": "System uploads the image to the AI service to identify food items and estimate nutritional content."
    },
    {
      "step": 4,
      "action": "View Summary Response",
      "description": "System returns a summary card displaying the identified food, estimated calories, and estimated sugar content."
    },
    {
      "step": 5,
      "action": "Save Record",
      "description": "User confirms the entry. The system saves the timestamp, calorie estimate, and sugar estimate to the local SQLite database."
    }
  ],
  "screens": [
    {
      "name": "DashboardScreen",
      "purpose": "Main hub showing daily progress and history.",
      "components": [
        "DailySummaryCard",
        "HistoryList",
        "FloatingActionButton"
      ]
    },
    {
      "name": "CaptureScreen",
      "purpose": "Interface for image input.",
      "components": [
        "CameraPreview",
        "GalleryButton",
        "UploadTrigger"
      ]
    },
    {
      "name": "ProcessingScreen",
      "purpose": "Interim state while AI analyzes the image.",
      "components": [
        "ActivityIndicator",
        "AnalysisStatusText"
      ]
    },
    {
      "name": "SummaryScreen",
      "purpose": "Displays the 'Summary Response' from the system for user verification.",
      "components": [
        "FoodImageThumbnail",
        "NutritionCard",
        "ConfirmButton",
        "DiscardButton"
      ]
    }
  ],
  "style_tokens": {
    "colors": {
      "primary": "#10B981",
      "primary_variant": "#059669",
      "secondary": "#3B82F6",
      "background": "#F9FAFB",
      "surface": "#FFFFFF",
      "text_primary": "#111827",
      "text_secondary": "#6B7280",
      "warning_sugar": "#EF4444",
      "success": "#34D399"
    },
    "typography": {
      "font_family": "Inter, sans-serif",
      "heading_1": "24px, Bold",
      "heading_2": "20px, SemiBold",
      "body": "16px, Regular",
      "caption": "14px, Regular"
    },
    "spacing": {
      "base": "4px",
      "card_padding": "16px",
      "screen_margin": "24px",
      "grid_gap": "12px"
    },
    "effects": {
      "card_shadow": "0 1px 3px rgba(0,0,0,0.1)",
      "border_radius": "12px"
    }
  }
}