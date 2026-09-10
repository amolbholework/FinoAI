from pydantic import BaseModel


class Lesson(BaseModel):
    id: str
    title: str
    description: str
    youtube_id: str
    source: str


class Module(BaseModel):
    id: str
    title: str
    level: str
    description: str
    lessons: list[Lesson]


class ProgressResponse(BaseModel):
    completed_lesson_ids: list[str]
    total_lesson_count: int


class ToggleLessonRequest(BaseModel):
    lesson_id: str
