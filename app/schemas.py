from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OwnerSetup(BaseModel):
    setup_key: str
    full_name: str = Field(min_length=2, max_length=120)
    national_code: str = Field(pattern=r"^\d{10}$")
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=10, max_length=128)


class Login(BaseModel):
    national_code: str = Field(pattern=r"^\d{10}$")
    password: str


class CustomerRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str = Field(min_length=8, max_length=32)
    national_code: str = Field(pattern=r"^\d{10}$")
    birth_date: date
    gender: str = Field(pattern="^(female|male|other)$")
    address: str = Field(min_length=5, max_length=1000)
    postal_code: str = Field(pattern=r"^\d{10}$")
    occupation: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=128)


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=32)
    birth_date: date | None = None
    gender: str | None = Field(default=None, pattern="^(female|male|other)$")
    address: str | None = Field(default=None, min_length=5, max_length=1000)
    postal_code: str | None = Field(default=None, pattern=r"^\d{10}$")
    occupation: str | None = Field(default=None, min_length=2, max_length=120)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    full_name: str
    email: EmailStr | None
    phone: str | None
    national_code: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    address: str | None = None
    postal_code: str | None = None
    occupation: str | None = None
    is_owner: bool
    is_active: bool

    @field_validator("email", mode="before")
    @classmethod
    def hide_internal_email(cls, value):
        if isinstance(value, str) and (value.endswith("@no-email.invalid") or (value.startswith("noemail-") and value.endswith("@example.com"))):
            return None
        return value


class FundCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    monthly_share: Decimal = Field(gt=0, max_digits=18, decimal_places=0)
    start_date: date
    payment_grace_days: int = Field(default=3, ge=2, le=3)
    max_members: int = Field(ge=2, le=100)
    currency: str = Field(default="IRT", min_length=3, max_length=8)


class FundOut(ORMModel):
    id: int
    name: str
    monthly_share: Decimal
    currency: str
    payment_grace_days: int
    max_members: int
    current_members: int
    end_date: date
    start_date: date
    status: str
    owner_id: int


class OpenFundOut(FundOut):
    available_slots: int


class MemberCreate(BaseModel):
    email: EmailStr | None = None
    national_code: str = Field(pattern=r"^\d{10}$")


class MemberOut(BaseModel):
    membership_id: int
    user_id: int
    full_name: str
    email: EmailStr | None
    national_code: str | None = None
    phone: str | None
    status: str
    joined_at: datetime


class MemberHistoryOut(BaseModel):
    membership_id: int
    joined_at: datetime
    days_in_fund: int
    previous_funds_count: int
    late_installments_count: int
    funds: list[dict]


class AdminUserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr | None
    phone: str | None
    national_code: str | None
    birth_date: date | None
    gender: str | None
    address: str | None
    postal_code: str | None
    occupation: str | None
    is_owner: bool
    is_active: bool
    created_at: datetime
    funds: list[dict]

    @field_validator("email", mode="before")
    @classmethod
    def hide_internal_email(cls, value):
        if isinstance(value, str) and (value.endswith("@no-email.invalid") or (value.startswith("noemail-") and value.endswith("@example.com"))):
            return None
        return value


class DrawOut(BaseModel):
    position: int
    membership_id: int
    member_name: str
    drawn_at: datetime


class StartFund(BaseModel):
    confirm_permanent_random_draw: bool = False


class PaymentUpdate(BaseModel):
    status: str = Field(pattern="^(pending|paid|late|coordinated|waived)$")
    payment_reference: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class CycleUpdate(BaseModel):
    status: str = Field(pattern="^(scheduled|paid|delayed|cancelled)$")


class InstallmentOut(ORMModel):
    id: int
    cycle_id: int
    membership_id: int
    amount: Decimal
    status: str
    due_date: date
    paid_at: datetime | None
    payment_reference: str | None
    note: str | None


class CycleOut(BaseModel):
    id: int
    number: int
    due_date: date
    recipient_membership_id: int
    recipient_name: str
    gross_amount: Decimal
    recipient_share: Decimal
    net_amount: Decimal
    status: str
    installments: list[InstallmentOut]
