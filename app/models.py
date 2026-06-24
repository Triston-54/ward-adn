"""SQLAlchemy ORM models and Pydantic schemas for API responses."""
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── ORM Models ──────────────────────────────────────────────────────────────


class UserProgress(Base):
    """Aggregate progress for the local student (single-user, local-first)."""

    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(String(128), default="ADN Student")
    program: Mapped[str] = mapped_column(String(256), default="New River CTC — ADN")
    overall_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    next_milestone_label: Mapped[str] = mapped_column(
        String(256), default="Start your first study session"
    )
    next_milestone_target: Mapped[float] = mapped_column(Float, default=10.0)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ModuleCompletion(Base):
    """Per-module completion tracking."""

    __tablename__ = "module_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    module_name: Mapped[str] = mapped_column(String(128))
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    items_completed: Mapped[int] = mapped_column(Integer, default=0)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ModuleProgress(Base):
    """Per-module progress tracking."""

    __tablename__ = "module_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    module_name: Mapped[str] = mapped_column(String(128))
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    items_completed: Mapped[int] = mapped_column(Integer, default=0)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class StudySession(Base):
    """Individual study session log."""

    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), index=True)
    activity_type: Mapped[str] = mapped_column(String(64))  # practice, flashcard, calculator
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserNote(Base):
    """User-created notes per module."""

    __tablename__ = "user_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class FlashcardState(Base):
    """Spaced-repetition state for flashcards."""

    __tablename__ = "flashcard_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), index=True)
    card_key: Mapped[str] = mapped_column(String(256), index=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0)


class UploadedFile(Base):
    """Uploaded syllabus / evaluation sheets."""

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512))
    original_name: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str] = mapped_column(String(64))  # syllabus, evaluation, other
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CustomTerm(Base):
    """User-added medical terminology entries."""

    __tablename__ = "custom_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(256), index=True)
    definition: Mapped[str] = mapped_column(Text)
    prefix: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    root: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    clinical_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ContentAuditRecord(Base):
    """Per-item content correctness audit status (local-first)."""

    __tablename__ = "content_audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[str] = mapped_column(String(64), index=True)
    item_key: Mapped[str] = mapped_column(String(256), index=True)
    item_type: Mapped[str] = mapped_column(String(64))  # concept, calculation, practice, etc.
    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="unreviewed", index=True)
    verified_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # YYYY-MM
    source_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SavedCalculation(Base):
    """User-saved favorite dosage calculations."""

    __tablename__ = "saved_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    calc_type: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(256))
    inputs_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Pydantic Schemas ────────────────────────────────────────────────────────


class SourceRef(BaseModel):
    """Verified source reference."""

    title: str
    url: Optional[str] = None
    citation: str
    verified_date: str = "2026-06"


class ModuleProgressOut(BaseModel):
    module_id: str
    module_name: str
    percentage: float
    items_completed: int
    items_total: int
    last_practiced: Optional[datetime] = None
    streak_days: int = 0

    model_config = {"from_attributes": True}


class UserProgressOut(BaseModel):
    display_name: str
    program: str
    overall_percentage: float
    current_streak: int
    longest_streak: int
    total_study_minutes: int
    next_milestone_label: str
    next_milestone_target: float
    last_synced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SyncProgressResponse(BaseModel):
    status: str
    message: str
    user: UserProgressOut
    modules: list[ModuleProgressOut]
    synced_at: datetime


class ProgressUpdate(BaseModel):
    module_id: str
    items_completed: Optional[int] = None
    items_total: Optional[int] = None
    activity_type: str = "practice"
    score: Optional[float] = None
    duration_seconds: int = 0


class ModuleProgressReport(BaseModel):
    """Shared payload for module activity progress POST endpoints."""

    items_studied: int = 1
    activity_type: str = "study"
    score: Optional[float] = None


class TermComponent(BaseModel):
    element: str
    meaning: str
    example: Optional[str] = None
    source: SourceRef


class MedicalTerm(BaseModel):
    term: str
    definition: str
    prefix: Optional[str] = None
    root: Optional[str] = None
    suffix: Optional[str] = None
    breakdown: Optional[str] = None
    clinical_relevance: Optional[str] = None
    category: str = "general"
    source: SourceRef


class WordBuildRequest(BaseModel):
    prefix: Optional[str] = ""
    root: str
    suffix: Optional[str] = ""


class WordBuildResult(BaseModel):
    built_term: str
    components: list[dict]
    likely_meaning: str
    clinical_note: str
    source: SourceRef


class PracticeQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    source: SourceRef
    nclex_category: Optional[str] = None


class DosageCalculationRequest(BaseModel):
    calc_type: str
    ordered_dose: Optional[float] = None
    available_dose: Optional[float] = None
    available_volume: Optional[float] = None
    patient_weight_kg: Optional[float] = None
    dose_per_kg: Optional[float] = None
    doses_per_day: Optional[float] = None
    volume_to_infuse_ml: Optional[float] = None
    time_minutes: Optional[float] = None
    drop_factor: Optional[float] = None
    geriatric_factor: Optional[float] = 0.75
    show_work: bool = True


class DosageWorkStep(BaseModel):
    step: str
    title: str
    formula: str
    reasoning: str
    result: str = ""


class DosageCalculationResult(BaseModel):
    answer: float
    unit: str
    steps: list[str]
    work_steps: list[DosageWorkStep] = Field(default_factory=list)
    derivation: str
    derivation_latex: str = ""
    derivation_result: str = ""
    clinical_note: str
    safety_warnings: list[str] = Field(default_factory=list)
    nursing_considerations: list[str] = Field(default_factory=list)
    pharmacology_note: str = ""
    calc_label: str = ""
    source: SourceRef


class CustomTermCreate(BaseModel):
    term: str
    definition: str
    prefix: Optional[str] = None
    root: Optional[str] = None
    suffix: Optional[str] = None
    clinical_note: Optional[str] = None


class CustomTermOut(BaseModel):
    id: int
    term: str
    definition: str
    prefix: Optional[str] = None
    root: Optional[str] = None
    suffix: Optional[str] = None
    clinical_note: Optional[str] = None
    is_favorite: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomTermFavoriteUpdate(BaseModel):
    is_favorite: bool


class SavedCalculationCreate(BaseModel):
    calc_type: str
    label: str
    inputs_json: str
    result_json: str


class SavedCalculationOut(BaseModel):
    id: int
    calc_type: str
    label: str
    inputs_json: str
    result_json: str
    is_favorite: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DosagePracticeCheck(BaseModel):
    problem_id: str
    selected_index: int


class AssessmentPracticeCheck(BaseModel):
    question_id: str
    selected_index: int
    selected_option: Optional[str] = None


class AssessmentScenarioCheck(BaseModel):
    scenario_id: str
    selected_index: int
    selected_option: Optional[str] = None


class AssessmentRedFlagDrillCheck(BaseModel):
    flag_id: str
    selected_index: int
    selected_option: Optional[str] = None


class MentalHealthDrillCheck(BaseModel):
    question_id: str
    selected_index: int
    selected_option: Optional[str] = None


class MaternalChildDrillCheck(BaseModel):
    question_id: str
    selected_index: int
    selected_option: Optional[str] = None


class AssessmentSoapValidate(BaseModel):
    exercise_id: str
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""


class AssessmentFlashcardReview(BaseModel):
    card_id: str
    quality: int  # 0=again, 1=hard, 2=good, 3=easy


class AuditVerifyRequest(BaseModel):
    verified_date: Optional[str] = None  # YYYY-MM
    source_note: Optional[str] = None


class AuditFlagRequest(BaseModel):
    review_note: str = Field(min_length=1, max_length=2000)


class AuditItemOut(BaseModel):
    module_id: str
    item_key: str
    item_type: str
    title: str
    subtitle: Optional[str] = None
    status: str = "unreviewed"
    verified_date: Optional[str] = None
    source_note: Optional[str] = None
    review_note: Optional[str] = None
    updated_at: Optional[datetime] = None


class AuditSummaryOut(BaseModel):
    total: int
    verified: int
    needs_review: int
    unreviewed: int
    by_module: dict[str, dict[str, int]]


class SocraticRequest(BaseModel):
    module_id: str
    question: str
    context: Optional[str] = None
    topic_category: Optional[str] = None  # pathophysiology, drug_mechanism, assessment_finding, calculation, general
    socratic_mode: bool = True
    intent: Optional[str] = None  # explore, explain_further, explain_mechanism, clinical_why, professional_considerations
    page_context: Optional[str] = None  # JSON: {tab, subject, snippet, track}


class SocraticResponse(BaseModel):
    response: str
    follow_up_questions: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    ai_status: str = "placeholder"
    phase: str = "explore"  # explore = guiding questions only; teach = deeper explanation allowed
    topic_category: str = "general"
    module_id: str = "general"
    guiding_only: bool = True
    intent: str = "explore"
    quick_actions: list[str] = Field(default_factory=list)
    degraded_reason: Optional[str] = None  # timeout | unavailable | empty_response