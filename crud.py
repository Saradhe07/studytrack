from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


# ---------- Student CRUD ----------

def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(
        name=student.name, email=student.email, age=student.age
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(db: Session, min_age: Optional[int] = None) -> list[models.Student]:
    query = db.query(models.Student)
    if min_age is not None:
        query = query.filter(models.Student.age >= min_age)
    return query.all()


def update_student(
    db: Session, student_id: int, updates: schemas.StudentUpdate
) -> Optional[models.Student]:
    db_student = get_student(db, student_id)
    if db_student is None:
        return None
    data = updates.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_student, field, value)
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: int) -> bool:
    db_student = get_student(db, student_id)
    if db_student is None:
        return False
    db.delete(db_student)
    db.commit()
    return True


def get_student_course_count(db: Session, student_id: int) -> int:
    # SELECT COUNT(*) via SQLAlchemy's func.count() -- an actual DB aggregate,
    # not len() over a Python list.
    return (
        db.query(func.count(models.Course.id))
        .filter(models.Course.student_id == student_id)
        .scalar()
    )


# ---------- Course CRUD ----------

def create_course(db: Session, course: schemas.CourseCreate) -> models.Course:
    db_course = models.Course(
        course_name=course.course_name,
        credits=course.credits,
        student_id=course.student_id,
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def get_course(db: Session, course_id: int) -> Optional[models.Course]:
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def get_courses(db: Session) -> list[models.Course]:
    return db.query(models.Course).all()


def update_course(
    db: Session, course_id: int, updates: schemas.CourseUpdate
) -> Optional[models.Course]:
    db_course = get_course(db, course_id)
    if db_course is None:
        return None
    data = updates.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_course, field, value)
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: int) -> bool:
    db_course = get_course(db, course_id)
    if db_course is None:
        return False
    db.delete(db_course)
    db.commit()
    return True