"""SQLAlchemy model with database-level constraints."""
from datetime import date, datetime, timezone
from sqlalchemy import CheckConstraint, Date, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (
        CheckConstraint("status IN ('todo', 'in_progress', 'done')", name='valid_status'),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name='valid_priority'),
        CheckConstraint('length(title) BETWEEN 1 AND 200', name='valid_title_length'),
        {'sqlite_autoincrement': True},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default='todo', index=True)
    priority: Mapped[str] = mapped_column(String(10), default='medium')
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # SQLite stores UTC without a timezone; response schemas restore the UTC offset.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
