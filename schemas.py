from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ---------- Student schemas ----------

class StudentBase(BaseModel):
    name: str
    email: str
    age: int = Field(gt=0)

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("email must contain an '@' character")
        return value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    # All optional -> supports PATCH-style partial updates
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and "@" not in value:
            raise ValueError("email must contain an '@' character")
        return value


class StudentRead(BaseModel):
    id: int
    name: str
    email: str
    age: int

    class Config:
        from_attributes = True


# ---------- Course schemas ----------

class CourseBase(BaseModel):
    course_name: str
    credits: int = Field(ge=1, le=6)
    student_id: int


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    credits: Optional[int] = Field(default=None, ge=1, le=6)
    student_id: Optional[int] = None


class CourseRead(BaseModel):
    id: int
    course_name: str
    credits: int
    student_id: int

    class Config:
        from_attributes = True


# ---------- AI Assistant schemas (Part 3) ----------

class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    topic: str
    key_points: list[str]
    difficulty: str


class NoteSearchResult(BaseModel):
    id: int
    text: str
    score: float
    matched_words: Optional[list[str]] = Field(default_factory=list)


class AddNoteRequest(BaseModel):
    text: str