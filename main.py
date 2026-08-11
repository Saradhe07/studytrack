"""
StudyTrack backend entrypoint.

Run mode chosen: SINGLE-PROCESS.
The frontend/ folder is mounted as static files at the bottom of this file,
so opening http://localhost:8000/ serves the dashboard, and every fetch()
in app.js uses a relative path like fetch("/students/") hitting this same
server. CORS is still configured below as standard practice.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional

import models
import schemas
import crud
import algorithms
import ai_service
import seed_data
from database import engine, Base, get_db, SessionLocal

# Create tables on startup if they don't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="StudyTrack API")

# CORS: never use "*". Explicitly allow the two-process dev origin
# (localhost:5500) even though this project runs single-process.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_database_on_startup():
    db = SessionLocal()
    try:
        seed_data.seed_if_empty(db)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------- Student routes ----------

@app.post("/students/", response_model=schemas.StudentRead, status_code=201)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_student(db, student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")


@app.get("/students/", response_model=list[schemas.StudentRead])
def list_students(
    min_age: Optional[int] = Query(default=None), db: Session = Depends(get_db)
):
    return crud.get_students(db, min_age=min_age)


# ---------- Algorithm-backed routes (Part 2) ----------
# NOTE: these must be declared BEFORE "/students/{student_id}" so FastAPI's
# path matching doesn't treat "sorted", "search", "report" as a student_id.

@app.get("/students/sorted")
def get_students_sorted(by: str = Query(default="age"), db: Session = Depends(get_db)):
    if by not in ("age", "name"):
        raise HTTPException(status_code=400, detail="`by` must be 'age' or 'name'")
    db_students = crud.get_students(db)
    student_dicts = [
        {"id": s.id, "name": s.name, "email": s.email, "age": s.age}
        for s in db_students
    ]
    algorithms.insertion_sort_by_field(student_dicts, by)
    return student_dicts


@app.get("/students/search")
def search_student_by_name(name: str, db: Session = Depends(get_db)):
    db_students = crud.get_students(db)
    student_dicts = [
        {"id": s.id, "name": s.name, "email": s.email, "age": s.age}
        for s in db_students
    ]
    name_sorted = sorted(student_dicts, key=lambda s: s["name"])
    result = algorithms.binary_search_by_name(name_sorted, name)
    if result == -1:
        raise HTTPException(status_code=404, detail="Student not found")
    return result


@app.get("/students/report")
def get_roster_report(min_age: int = Query(default=21), db: Session = Depends(get_db)):
    db_students = crud.get_students(db)
    student_dicts = [
        {"id": s.id, "name": s.name, "email": s.email, "age": s.age}
        for s in db_students
    ]
    report = algorithms.format_roster_report(student_dicts)
    count = algorithms.count_students_meeting_min_age(student_dicts, min_age)
    return {"report": report, "count_meeting_min_age": count}


# ---------- Student routes (continued) ----------

@app.get("/students/{student_id}", response_model=schemas.StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    db_student = crud.get_student(db, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@app.patch("/students/{student_id}", response_model=schemas.StudentRead)
def update_student(
    student_id: int, updates: schemas.StudentUpdate, db: Session = Depends(get_db)
):
    try:
        db_student = crud.update_student(db, student_id, updates)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_student(db, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"detail": "Student deleted"}


@app.get("/students/{student_id}/course-count")
def student_course_count(student_id: int, db: Session = Depends(get_db)):
    db_student = crud.get_student(db, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    count = crud.get_student_course_count(db, student_id)
    return {"student_id": student_id, "course_count": count}


# ---------- Course routes ----------

@app.post("/courses/", response_model=schemas.CourseRead, status_code=201)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    return crud.create_course(db, course)


@app.get("/courses/", response_model=list[schemas.CourseRead])
def list_courses(db: Session = Depends(get_db)):
    return crud.get_courses(db)


@app.get("/courses/{course_id}", response_model=schemas.CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)):
    db_course = crud.get_course(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return db_course


@app.patch("/courses/{course_id}", response_model=schemas.CourseRead)
def update_course(
    course_id: int, updates: schemas.CourseUpdate, db: Session = Depends(get_db)
):
    db_course = crud.update_course(db, course_id, updates)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return db_course


@app.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_course(db, course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"detail": "Course deleted"}


# ---------- AI Assistant routes (Part 3) ----------

@app.get("/assistant/mode")
def get_assistant_mode():
    return {"mode": ai_service.get_ai_mode()}


@app.post("/assistant/summarize", response_model=schemas.SummarizeResponse)
def summarize_study_notes(payload: schemas.SummarizeRequest):
    return ai_service.summarize_notes(payload.text)


@app.get("/assistant/search", response_model=list[schemas.NoteSearchResult])
def search_study_notes(query: str = Query(default="")):
    return ai_service.search_notes(query)


@app.get("/assistant/notes")
def list_study_notes():
    return ai_service.get_all_notes()


@app.post("/assistant/notes", status_code=201)
def add_custom_study_note(payload: schemas.AddNoteRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Note text cannot be empty.")
    return ai_service.add_custom_note(payload.text)



import os

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")