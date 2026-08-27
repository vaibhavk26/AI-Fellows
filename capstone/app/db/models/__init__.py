"""Database models package."""

from app.db.models.user import StudentProfile, TeacherProfile, User  # noqa: F401
from app.db.models.curriculum import Chapter, CurriculumDocument, SourceReference, Subject, Topic  # noqa: F401
from app.db.models.question import Question, QuestionSourceReference, QuestionValidationResult  # noqa: F401
from app.db.models.exam import Exam, ExamQuestion  # noqa: F401
from app.db.models.attempt import StudentAnswer, StudentAttempt  # noqa: F401
from app.db.models.analytics import TopicPerformance  # noqa: F401
from app.db.models.extensions import Badge, ExamAssignment, PracticeRecommendation, StudentBadge  # noqa: F401

