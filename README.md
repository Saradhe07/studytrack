# StudyTrack — Unified Full-Stack Study Management Platform

StudyTrack is a unified full-stack study management platform built for Myntra's internal Trainee Enablement team. It integrates a live Student and Course roster powered by FastAPI and SQLite (SQLAlchemy ORM), a hand-rolled algorithms engine for sorting and searching, and an offline-first AI Assistant module for note summarization and semantic note search via vector embeddings and cosine similarity.

---

## 1. Run Mode & Setup Instructions

### Run Mode Choice: Single-Process (Recommended)

This application operates in **Single-Process mode**. The FastAPI backend serves the `frontend/` directory as static files via `app.mount("/", StaticFiles(directory=frontend_dir, html=True))`.

- Opening `http://localhost:8000/` in a web browser directly loads the interactive dashboard.
- Every API call in `app.js` uses relative paths (e.g. `fetch("/students/")`, `fetch("/courses/")`), targeting the same origin.
- CORS middleware is explicitly configured with `allow_origins=["http://localhost:5500", "http://localhost:8000"]` to allow local two-process frontend development while maintaining strict origin rules (wildcard `*` is never used).

### Setup and Running Instructions

1. **Navigate to backend directory**:
```bash
   cd backend
```

2. **Create and activate virtual environment**:

   On Windows (PowerShell):
```powershell
   python -m venv venv
   .\venv\Scripts\activate
```

   On Linux/macOS:
```bash
   source venv/bin/activate
```

3. **Install dependencies**:
```bash
   pip install -r requirements.txt
```

4. **Start the single-process application**:
```bash
   uvicorn main:app --reload --port 8000
```

5. **Open Dashboard & API Docs**:
   - Web Dashboard: http://localhost:8000/
   - Swagger API Documentation: http://localhost:8000/docs

On initial startup, the database is automatically seeded with the exact 8 seed student records and sample course enrollments if empty.

---

## 2. Comprehensive API Endpoint Documentation

### Core Student & Course Endpoints (Part 1)

| Method | Path | Request Body | Response Shape | Description |
|---|---|---|---|---|
| POST | `/students/` | `{"name": str, "email": str, "age": int}` | `StudentRead` (id, name, email, age) | Create a new student. Validates email `@` and age > 0. |
| GET | `/students/` | None (Optional `?min_age=int`) | List of `StudentRead` | List all students. Filters `age >= min_age` when parameter provided. |
| GET | `/students/{id}` | None | `StudentRead` | Fetch a single student record (404 if not found). |
| PATCH | `/students/{id}` | `{"name"?: str, "email"?: str, "age"?: int}` | `StudentRead` | Partial update of student details (404 if not found). |
| DELETE | `/students/{id}` | None | `{"detail": "Student deleted"}` | Delete student record (404 if not found). |
| GET | `/students/{id}/course-count` | None | `{"student_id": int, "course_count": int}` | Returns enrollment count computed via DB aggregate (`func.count`). |
| POST | `/courses/` | `{"course_name": str, "credits": int, "student_id": int}` | `CourseRead` (id, course_name, credits, student_id) | Create course enrollment (credits validated 1..6). |
| GET | `/courses/` | None | List of `CourseRead` | List all course enrollments. |
| GET | `/courses/{id}` | None | `CourseRead` | Fetch course details (404 if not found). |
| PATCH | `/courses/{id}` | `{"course_name"?: str, "credits"?: int, "student_id"?: int}` | `CourseRead` | Partial update of course enrollment (404 if not found). |
| DELETE | `/courses/{id}` | None | `{"detail": "Course deleted"}` | Delete course enrollment (404 if not found). |

**SQL Aggregate Note:** `GET /students/{id}/course-count` executes `db.query(func.count(models.Course.id)).filter(models.Course.student_id == student_id).scalar()` directly in SQLite. It does not load rows into Python to use `len()`.

### Integrated Algorithms Engine Endpoints (Part 2)

| Method | Path | Query Parameters | Response Shape | Description |
|---|---|---|---|---|
| GET | `/students/sorted` | `by=age` or `by=name` | List of Student Dicts | Returns roster sorted in-place via hand-written Insertion Sort. |
| GET | `/students/search` | `name=str` | Student Dict | Hand-written Binary Search over alphabetically sorted roster (404 if not found). |
| GET | `/students/report` | `min_age=int` (default 21) | `{"report": str, "count_meeting_min_age": int}` | Generates formatted multiline report and count of students matching `min_age`. |

### Integrated AI Assistant Endpoints (Part 3)

| Method | Path | Request Body | Response Shape | Description |
|---|---|---|---|---|
| POST | `/assistant/summarize` | `{"text": str}` | `{"topic": str, "key_points": list[str], "difficulty": str}` | Summarizes notes deterministically into structured JSON. |
| GET | `/assistant/search` | `query=str` | List of `{"id": int, "text": str, "score": float}` | Ranks sample notes by cosine similarity using 12-dim mock embeddings. |

---

## 3. Algorithm Complexity Write-Up (Part 2)

### Insertion Sort: O(n²) Worst-Case vs. O(n) Best-Case Complexity

Hand-written Insertion Sort (`insertion_sort_by_field`) iterates through the list starting from the second element, placing each element into its sorted position among previously processed elements.

- **Best Case O(n):** Occurs when the input roster is already sorted ascending by the requested field (age or name). On each outer iteration, the inner `while` condition (`students[j][field] > key[field]`) evaluates to False on the very first comparison. No element shifting occurs, resulting in n − 1 total comparisons and linear time complexity.
- **Worst Case O(n²):** Occurs when the input roster is in reverse sorted order. Every outer pass requires shifting all i previously placed elements to the right. The total number of shifts is Σ(i=1 to n-1) i = n(n-1)/2, resulting in quadratic time complexity.

### Binary Search: Requirement for Pre-Sorted Array

Hand-written Binary Search (`binary_search_by_name`) operates by calculating the midpoint index (`mid = low + (high - low) // 2`) and comparing the target name against `sorted_by_name_list[mid]["name"]`. Binary Search requires the input array to be sorted by the search field because it relies on the order property to eliminate half of the search space at each iteration. If the target is smaller than the midpoint value, all elements to the right of `mid` are guaranteed to be larger and can be safely discarded. If the array were unsorted, comparing a target against an arbitrary midpoint element would yield no information regarding which half contains the target value.

---

## 4. AI Assistant Design & Implementation (Part 3)

### Operating Mode: Offline Mock Mode (`AI_MODE=mock`)

The AI Assistant operates by default in fully offline mock mode. It requires no third-party API keys, network calls, or external service dependencies, ensuring 100% reliable execution.

### Task 1: Note Summarizer (`summarize_notes`)

Extracts structured notes deterministically:

- **Topic:** Derived as the first sentence of the first non-empty line of text. If input is empty or whitespace-only, defaults to `"untitled"`.
- **Key Points:** Extracted by splitting text into sentences on `.`, `!`, and `?` delimiters, stripping whitespace, and taking up to the first 3 non-empty sentences. Empty input yields `[]`.
- **Difficulty:** Evaluated based on total word count:
  - < 40 words → `"easy"`
  - 40–100 words → `"medium"`
  - \> 100 words → `"hard"` (Empty input has word count 0, which falls under < 40 words → `"easy"`).

### Real LLM Prompt Specification

If `AI_MODE=real` were configured with a chat completion API (e.g. OpenAI GPT-4o or Gemini API), the following structured prompt template is used:

```text
System: You are an expert educational AI assistant.
Task: Summarize raw study notes into a fixed structured JSON object.
Constraints: Output ONLY raw valid JSON matching the exact schema below. Do not include markdown fences or surrounding commentary.
Format Instructions:
{
  "topic": "<Concise topic title or main subject>",
  "key_points": ["<Key sentence 1>", "<Key sentence 2>", "<Key sentence 3>"],
  "difficulty": "<easy | medium | hard>"
}
User Input:
{raw_text}
```

### Task 3 & 4: Mock Embeddings & Cosine Similarity

- **`mock_embed(text)`:** Tokenizes lowercased input text by splitting on any non-alphanumeric character sequence (`re.split(r'[^a-z0-9]+', text.lower())`). Matches exact whole tokens against the fixed 12-word vocabulary: `["sort", "search", "binary", "insertion", "sql", "join", "fastapi", "pydantic", "prompt", "llm", "database", "validate"]`. Returns a 12-dimensional numeric vector representing token frequency counts.
- **`cosine_similarity(vec_a, vec_b)`:** Calculates `(a · b) / (|a| |b|)` using Python's `math.sqrt`. If either vector has an L2 norm of 0.0 (zero-vector edge case), it directly returns 0.0 to prevent `ZeroDivisionError`. Self-similarity `cosine_similarity(v, v)` for any non-zero vector returns 1.0.

---

## 5. End-to-End Walkthrough & Feature Verification

1. **Launch Application:** Run `uvicorn main:app --reload` from `backend/`. Open `http://localhost:8000/`.
2. **View Seed Roster:** The dashboard loads the 8 seed students (Aditi Rao, Rohan Mehta, Kavya Nair, Farhan Sheikh, Priya Iyer, Devansh Gupta, Meera Joshi, Sameer Khan).
3. **Insertion Sort:** Select `Age (Insertion Sort)` from the dropdown. The roster instantly orders by age ascending: Farhan (18), Rohan (19), Meera (20), Priya (21), Aditi (22), Devansh (23), Sameer (24), Kavya (25).
4. **Binary Search:** Type `Priya Iyer` into the search box and click Binary Search. The roster narrows to Priya Iyer's record.
5. **Update Student Age:** On Priya Iyer's card, change the age input to `22` and click Save Age. A `PATCH /students/{id}` request is sent and the displayed age updates immediately without page reload.
6. **Add Student:** Fill out the Add New Student form with Name: `Ananya Roy`, Email: `ananya.roy@example.com`, Age: `20`. Click Add Student. A `POST /students/` request runs and a new student card appears dynamically in the DOM via `document.createElement`.
7. **Enroll Student in Course:** Navigate to `#course-section`. Select `Aditi Rao` in the student dropdown, type Course Name: `Algorithms & Data Structures`, Credits: `4`. Click Enroll Course. A `POST /courses/` request is issued and the new course appears under Active Course Enrollments.
8. **Inspect Aggregate Course Count:** In `#course-section`, select `Aditi Rao` and click Inspect Count. The app calls `GET /students/1/course-count` and displays the aggregate count (e.g. 3 courses enrolled via SQL `func.count()`).
9. **Delete Course Enrollment:** Click Delete on a course card under Active Course Enrollments. A `DELETE /courses/{id}` request is sent and the enrollment is removed.
10. **Delete Student:** Click Delete on Ananya Roy's card. A `DELETE /students/{id}` request runs and the card is removed from the DOM.
11. **AI Note Summarizer:** In the AI Helper panel, paste notes into the textarea and click Summarize Notes. Topic, Key Points, and Difficulty badge render on the page.
12. **Semantic Note Search:** Type `binary search algorithm` in the search query box and click Search Notes. Note #1 ("Binary search requires a sorted array...") ranks at top with similarity score `1.0000`.

---

## 6. Git Workflow Compliance

This repository strictly adheres to standard branch/merge Git workflow rules:

- Main branch: `main`
- Feature branch: `feature/ai-assistant-integration` created for Part 3 implementation.
- Multiple commits made on feature branch covering backend `ai_service.py`, FastAPI endpoints, and frontend integration.
- Feature branch merged back into `main`.
- No API keys or sensitive credentials are committed. `.env.example` is committed to illustrate environment configuration.
