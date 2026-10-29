from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    national_code: Mapped[str | None] = mapped_column(String(10), nullable=True, unique=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Fund(Base):
    __tablename__ = "funds"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    monthly_share: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    currency: Mapped[str] = mapped_column(String(8), default="IRT")
    payment_grace_days: Mapped[int] = mapped_column(Integer, default=3)
    max_members: Mapped[int] = mapped_column(Integer, default=10)
    current_members: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def end_date(self) -> date:
        month_index = self.start_date.month - 1 + self.max_members - 1
        year, month = self.start_date.year + month_index // 12, month_index % 12 + 1
        return self.start_date.replace(year=year, month=month, day=min(self.start_date.day, monthrange(year, month)[1]))


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("fund_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped[User] = relationship()
    fund: Mapped[Fund] = relationship()


class DrawEntry(Base):
    __tablename__ = "draw_entries"
    __table_args__ = (UniqueConstraint("fund_id", "membership_id"), UniqueConstraint("fund_id", "position"))
    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"), index=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    position: Mapped[int] = mapped_column(Integer)
    drawn_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    membership: Mapped[Membership] = relationship()


class Cycle(Base):
    __tablename__ = "cycles"
    __table_args__ = (UniqueConstraint("fund_id", "number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date)
    recipient_membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    recipient_share: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    recipient: Mapped[Membership] = relationship()


class Installment(Base):
    __tablename__ = "installments"
    __table_args__ = (UniqueConstraint("cycle_id", "membership_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id", ondelete="CASCADE"), index=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    due_date: Mapped[date] = mapped_column(Date)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    membership: Mapped[Membership] = relationship()
    cycle: Mapped[Cycle] = relationship()
