from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    age = Column(Integer, nullable=False)

    # student.courses -> list of Course rows enrolled to this student
    courses = relationship(
        "Course", back_populates="student", cascade="all, delete-orphan"
    )


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # course.student -> the single Student row that owns this enrollment
    student = relationship("Student", back_populates="courses")

    __table_args__ = (
        CheckConstraint("credits >= 1 AND credits <= 6", name="check_credits_range"),
    )