from sqlalchemy.orm import Session

import models

SEED_STUDENTS = [
    {"name": "Aditi Rao",     "email": "aditi.rao@example.com",     "age": 22},
    {"name": "Rohan Mehta",   "email": "rohan.mehta@example.com",   "age": 19},
    {"name": "Kavya Nair",    "email": "kavya.nair@example.com",    "age": 25},
    {"name": "Farhan Sheikh", "email": "farhan.sheikh@example.com", "age": 18},
    {"name": "Priya Iyer",    "email": "priya.iyer@example.com",    "age": 21},
    {"name": "Devansh Gupta", "email": "devansh.gupta@example.com", "age": 23},
    {"name": "Meera Joshi",   "email": "meera.joshi@example.com",   "age": 20},
    {"name": "Sameer Khan",   "email": "sameer.khan@example.com",   "age": 24},
]

SEED_COURSES = [
    {"course_name": "Data Structures & Algorithms", "credits": 4, "student_index": 0}, # Aditi Rao
    {"course_name": "FastAPI Backend Engineering",   "credits": 3, "student_index": 0}, # Aditi Rao (Count = 2)
    {"course_name": "Python Programming",           "credits": 3, "student_index": 1}, # Rohan Mehta
    {"course_name": "Machine Learning Foundations",  "credits": 5, "student_index": 2}, # Kavya Nair
    {"course_name": "Database Systems & SQL",       "credits": 4, "student_index": 2}, # Kavya Nair (Count = 2)
]


def seed_if_empty(db: Session) -> None:
    """Insert SEED_STUDENTS and SEED_COURSES if tables are empty."""
    existing_students = db.query(models.Student).count()
    if existing_students == 0:
        created_students = []
        for record in SEED_STUDENTS:
            db_student = models.Student(
                name=record["name"], email=record["email"], age=record["age"]
            )
            db.add(db_student)
            created_students.append(db_student)
        db.commit()

        for s in created_students:
            db.refresh(s)

        for course_data in SEED_COURSES:
            student = created_students[course_data["student_index"]]
            db_course = models.Course(
                course_name=course_data["course_name"],
                credits=course_data["credits"],
                student_id=student.id,
            )
            db.add(db_course)
        db.commit()
    else:
        # Check if course table is empty and seed courses if needed
        existing_courses = db.query(models.Course).count()
        if existing_courses == 0:
            students = db.query(models.Student).order_by(models.Student.id).all()
            if len(students) >= 3:
                c1 = models.Course(course_name="Data Structures & Algorithms", credits=4, student_id=students[0].id)
                c2 = models.Course(course_name="FastAPI Backend Engineering", credits=3, student_id=students[0].id)
                c3 = models.Course(course_name="Python Programming", credits=3, student_id=students[1].id)
                c4 = models.Course(course_name="Machine Learning Foundations", credits=5, student_id=students[2].id)
                c5 = models.Course(course_name="Database Systems & SQL", credits=4, student_id=students[2].id)
                db.add_all([c1, c2, c3, c4, c5])
                db.commit()