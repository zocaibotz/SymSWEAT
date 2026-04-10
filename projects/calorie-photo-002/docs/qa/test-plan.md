# Test Plan: Calorie Photo Tracker (V1)

Based on the architecture document, this test plan focuses on validating the V1 functionality, specifically the integration between the FastAPI gateway, the mocked AI service, the nutrition logic, and the SQLite database.

## 1. Test Strategy

*   **Unit Tests**: Testing isolated logic for Nutrition Estimator and Data Parsing.
*   **Integration Tests**: Testing API endpoints against the SQLite database (using a test instance).
*   **Mocking**: The Google Cloud Vision API will be mocked for local testing to ensure deterministic results.

---

## 2. Component-Level Test Cases

### 2.1 API Gateway (FastAPI)
*Focus: Request validation, routing, and error handling.*

| Test ID | Description | Test Data | Expected Result |
|---------|-------------|-----------|-----------------|
| **API-01** | Valid Image Upload | JPEG file, 2MB | 200 OK, JSON with food data |
| **API-02** | Invalid File Type | `.txt` or `.gif` | 400 Bad Request ("Invalid file format") |
| **API-03** | File Size Exceeded | Image > 10MB | 413 Payload Too Large |
| **API-04** | Missing File in Request | No file part | 422 Unprocessable Entity |
| **API-05** | Get Daily Summary | Valid date | 200 OK, correct totals |

### 2.2 Photo Upload Handler
*Focus: File system interaction and validation.*

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| **UPL-01** | File naming convention | File saved as `{timestamp}_{uuid}.{ext}` in `/uploads` |
| **UPL-02** | Directory creation | `/uploads` directory created if missing |

### 2.3 AI Service (Vision API Wrapper)
*Focus: Response parsing and error handling.*

| Test ID | Description | Mock Input | Expected Result |
|---------|-------------|------------|-----------------|
| **AI-01** | Parse successful response | JSON with `food_items` | Returns list of food names |
| **AI-02** | Handle empty response | Empty labels | Raises/Returns error indicating "No food identified" |
| **AI-03** | Confidence threshold | Items with 0.10 confidence | Logic to filter or flag low confidence |

### 2.4 Nutrition Estimator
*Focus: Business logic and math.*

| Test ID | Description | Input | Expected Result |
|---------|-------------|-------|-----------------|
| **NUT-01** | Single item calculation | "Pizza" (800 cal, 40g sugar) | `total_calories: 800`, `total_sugar: 40` |
| **NUT-02** | Multiple item aggregation | "Pizza" + "Cola" | Summation of both items |
| **NUT-03** | Unknown food fallback | "Unknown Dish" | Uses default "Estimated Meal" values (check config) |
| **NUT-04** | Empty food list | `[]` | Returns 0 calories, 0 sugar |

---

## 3. Integration & E2E Test Scenarios

### 3.1 Database Persistence (SQLite)
*Focus: Data integrity and retrieval.*

| Test ID | Description | Validation |
|---------|-------------|------------|
| **DB-01** | Save Log | After uploading, check `food_logs` table row count increases by 1. |
| **DB-02** | Data Integrity | Verify `food_items` column stores valid JSON. |
| **DB-03** | Summary Query | Sum of calories for a specific date matches sum of individual entries. |

### 3.2 End-to-End (Happy Path)
*Focus: Full data flow.*

1.  **Step 1**: Client sends `POST /api/v1/photo/upload` with a photo of a pizza.
2.  **Step 2**: System validates file -> Saves to disk -> Calls AI (Mock) -> AI returns "Pizza".
3.  **Step 3**: Nutrition Estimator looks up "Pizza" (e.g., 285kcal).
4.  **Step 4**: System inserts record into SQLite.
5.  **Step 5**: API returns success JSON with ID.
6.  **Verification**: Call `GET /api/v1/summary/{today}`. Total calories must include the pizza.

### 3.3 End-to-End (Error Path)
*Focus: Robustness.*

1.  **Step 1**: Upload a corrupted image file.
2.  **Step 2**: Upload Handler validates magic bytes -> Rejects -> Returns 400.
3.  **Verification**: Database should *not* have a new entry.

---

## 4. Security & Validation Tests

| Test ID | Area | Description |
|---------|------|-------------|
| **SEC-01** | Input Validation | Upload file with path traversal name (e.g., `../../app/main.py`). Ensure system sanitizes the filename. |
| **SEC-02** | Limit Enforcement | Attempt to upload 10.1MB file. Ensure truncation or rejection occurs before memory loading. |

---

## 5. Test Data Requirements

To execute this plan, the following test data is required:
1.  **Sample Images**: `pizza.jpg`, `salad.png`, `corrupt.jpg`, `large_file.jpg` (>10MB).
2.  **Mock Data**: A JSON fixture mimicking the Google Vision API response structure.
3.  **Nutrition DB Seed**: A seed script to populate the SQLite database with initial food items (e.g., Pizza, Apple, Cola).