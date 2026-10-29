from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import current_user, owned_fund, owner_user
from app.models import Cycle, DrawEntry, Fund, Installment, Membership, User
from app.schemas import AdminUserOut, CycleOut, CycleUpdate, DrawOut, FundCreate, FundOut, InstallmentOut, MemberCreate, MemberHistoryOut, MemberOut, OpenFundOut, PaymentUpdate, StartFund

router = APIRouter(prefix="/funds", tags=["صندوق و اعضا"])


def manager_members(fund_id: int, db: Session) -> list[Membership]:
    return list(db.scalars(select(Membership).options(joinedload(Membership.user)).where(
        Membership.fund_id == fund_id, Membership.status == "active"
    ).order_by(Membership.id)))


def member_output(member: Membership) -> MemberOut:
    return MemberOut(membership_id=member.id, user_id=member.user.id, full_name=member.user.full_name,
                     email=member.user.email, national_code=member.user.national_code,
                     phone=member.user.phone, status=member.status, joined_at=member.joined_at)


def add_months(day, offset: int):
    month_index = day.month - 1 + offset
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, monthrange(year, month)[1]))


@router.post("", response_model=FundOut, status_code=201)
def create_fund(data: FundCreate, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = Fund(**data.model_dump(), owner_id=owner.id, current_members=1)
    db.add(fund)
    db.flush()
    db.add(Membership(fund_id=fund.id, user_id=owner.id))
    db.commit()
    db.refresh(fund)
    return fund


@router.get("", response_model=list[FundOut])
def list_funds(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.is_owner:
        return list(db.scalars(select(Fund).where(Fund.owner_id == user.id).order_by(Fund.id)))
    return list(db.scalars(select(Fund).join(Membership).where(Membership.user_id == user.id, Membership.status != "removed").order_by(Fund.id)))


@router.get("/open", response_model=list[OpenFundOut])
def list_open_funds(db: Session = Depends(get_db), user: User = Depends(current_user)):
    funds = db.scalars(select(Fund).where(
        Fund.status == "draft", Fund.current_members < Fund.max_members
    ).order_by(Fund.created_at.desc()))
    result = []
    for fund in funds:
        enrolled = db.scalar(select(Membership.id).where(
            Membership.fund_id == fund.id, Membership.user_id == user.id
        ))
        if not enrolled:
            result.append(OpenFundOut.model_validate({
                **FundOut.model_validate(fund).model_dump(),
                "available_slots": fund.max_members - fund.current_members,
            }))
    return result


@router.post("/{fund_id}/join", response_model=FundOut, status_code=201)
def join_fund(fund_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    fund = db.get(Fund, fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="صندوق پیدا نشد")
    if fund.status != "draft":
        raise HTTPException(status_code=409, detail="ثبت‌نام این صندوق بسته شده است")
    if db.scalar(select(Membership.id).where(Membership.fund_id == fund_id, Membership.user_id == user.id)):
        raise HTTPException(status_code=409, detail="شما قبلاً در این صندوق ثبت‌نام کرده‌اید")
    reserved = db.execute(update(Fund).where(
        Fund.id == fund_id, Fund.status == "draft", Fund.current_members < Fund.max_members
    ).values(current_members=Fund.current_members + 1))
    if reserved.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="ظرفیت صندوق تکمیل شده است")
    db.add(Membership(fund_id=fund_id, user_id=user.id))
    db.commit()
    db.refresh(fund)
    return fund


@router.post("/{fund_id}/members", response_model=MemberOut, status_code=201)
def add_member(fund_id: int, data: MemberCreate, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = owned_fund(fund_id, owner, db)
    if fund.status != "draft" or db.scalar(select(DrawEntry.id).where(DrawEntry.fund_id == fund_id)):
        raise HTTPException(status_code=409, detail="اعضا پس از انجام قرعه‌کشی قابل تغییر نیستند")
    national_code = data.national_code.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    user = db.scalar(select(User).where(User.national_code == national_code))
    if not user:
        raise HTTPException(status_code=404, detail="حساب فعالی با این کد ملی پیدا نشد؛ کاربر باید ابتدا ثبت‌نام کند")
    if not user.is_active:
        raise HTTPException(status_code=409, detail="حساب این کاربر غیرفعال است")
    if data.email and (not user.email or user.email.lower() != data.email.lower()):
        raise HTTPException(status_code=409, detail="ایمیل واردشده با حساب این کد ملی مطابقت ندارد")
    if db.scalar(select(Membership.id).where(Membership.fund_id == fund.id, Membership.user_id == user.id)):
        raise HTTPException(status_code=409, detail="این کاربر قبلاً در این صندوق ثبت‌نام کرده است")
    reserved = db.execute(update(Fund).where(
        Fund.id == fund.id, Fund.status == "draft", Fund.current_members < Fund.max_members
    ).values(current_members=Fund.current_members + 1))
    if reserved.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="ظرفیت صندوق تکمیل شده است")
    member = Membership(fund_id=fund.id, user_id=user.id)
    db.add(member)
    db.commit()
    db.refresh(member)
    member.user = user
    return member_output(member)


@router.get("/{fund_id}/members", response_model=list[MemberOut])
def list_members(fund_id: int, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    owned_fund(fund_id, owner, db)
    members = db.scalars(select(Membership).options(joinedload(Membership.user)).where(
        Membership.fund_id == fund_id, Membership.status != "removed"
    ).order_by(Membership.id))
    return [member_output(m) for m in members]


@router.get("/{fund_id}/members/{membership_id}/history", response_model=MemberHistoryOut)
def member_history(fund_id: int, membership_id: int, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    owned_fund(fund_id, owner, db)
    member = db.scalar(select(Membership).options(joinedload(Membership.user)).where(
        Membership.id == membership_id, Membership.fund_id == fund_id
    ))
    if not member:
        raise HTTPException(status_code=404, detail="عضو پیدا نشد")
    memberships = list(db.scalars(select(Membership).options(joinedload(Membership.fund)).where(Membership.user_id == member.user_id)))
    history = []
    late_count = 0
    for item in memberships:
        installments = list(db.scalars(select(Installment).join(Cycle).where(
            Cycle.fund_id == item.fund_id, Installment.membership_id == item.id
        )))
        item_late = sum(1 for installment in installments if installment.status == "late")
        late_count += item_late
        history.append({"fund_id": item.fund_id, "fund_name": item.fund.name, "fund_status": item.fund.status,
                        "membership_status": item.status, "joined_at": item.joined_at,
                        "late_installments_count": item_late, "installments_count": len(installments)})
    ended_at = member.ended_at or datetime.now(timezone.utc)
    return MemberHistoryOut(membership_id=member.id, joined_at=member.joined_at,
                            days_in_fund=max(0, (ended_at.date() - member.joined_at.date()).days),
                            previous_funds_count=sum(1 for item in memberships if item.fund_id != fund_id),
                            late_installments_count=late_count, funds=history)


@router.get("/admin/users", response_model=list[AdminUserOut])
def search_users_by_national_code(national_code: str = Query(min_length=1, max_length=10),
                                  db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    normalized = national_code.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    if not normalized.isdigit():
        raise HTTPException(status_code=422, detail="کد ملی باید فقط شامل رقم باشد")
    users = list(db.scalars(select(User).where(User.national_code.contains(normalized)).order_by(User.created_at.desc())))
    result = []
    for user in users:
        memberships = list(db.scalars(select(Membership).options(joinedload(Membership.fund)).where(Membership.user_id == user.id)))
        user_funds = []
        for item in memberships:
            installments = list(db.scalars(select(Installment).join(Cycle).where(
                Cycle.fund_id == item.fund_id, Installment.membership_id == item.id
            ).order_by(Installment.due_date)))
            received = list(db.scalars(select(Cycle).where(
                Cycle.fund_id == item.fund_id, Cycle.recipient_membership_id == item.id
            ).order_by(Cycle.number)))
            user_funds.append({"fund_id": item.fund_id, "fund_name": item.fund.name, "fund_status": item.fund.status,
                               "membership_status": item.status, "joined_at": item.joined_at,
                               "loans_received": len(received),
                               "received_loans": [{"number": c.number, "due_date": c.due_date, "net_amount": c.net_amount, "status": c.status} for c in received],
                               "installments_count": len(installments),
                               "late_installments_count": sum(1 for x in installments if x.status == "late"),
                               "installments": [{"cycle_id": x.cycle_id, "amount": x.amount, "due_date": x.due_date,
                                                 "status": x.status, "paid_at": x.paid_at,
                                                 "payment_reference": x.payment_reference, "note": x.note} for x in installments]})
        result.append(AdminUserOut(id=user.id, full_name=user.full_name, email=user.email, phone=user.phone,
                                   national_code=user.national_code, birth_date=user.birth_date, gender=user.gender,
                                   address=user.address, postal_code=user.postal_code, occupation=user.occupation,
                                   is_owner=user.is_owner, is_active=user.is_active, created_at=user.created_at,
                                   funds=user_funds))
    return result


@router.patch("/{fund_id}/members/{membership_id}", response_model=MemberOut)
def update_member(fund_id: int, membership_id: int, status: str, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = owned_fund(fund_id, owner, db)
    if status not in {"active", "paused", "removed"}:
        raise HTTPException(status_code=422, detail="وضعیت عضو نامعتبر است")
    member = db.scalar(select(Membership).options(joinedload(Membership.user)).where(Membership.id == membership_id, Membership.fund_id == fund_id))
    if not member:
        raise HTTPException(status_code=404, detail="عضو پیدا نشد")
    if status != "removed" and (fund.status != "draft" or db.scalar(select(DrawEntry.id).where(DrawEntry.fund_id == fund_id))):
        raise HTTPException(status_code=409, detail="پس از قرعه‌کشی فقط می‌توان عضویت را حذف کرد")
    if member.status == "removed" and status != "removed":
        raise HTTPException(status_code=409, detail="عضویت حذف‌شده قابل بازگردانی نیست؛ عضو را دوباره اضافه کنید")
    if member.status != "active" and status == "active":
        reserved = db.execute(update(Fund).where(
            Fund.id == fund.id, Fund.status == "draft", Fund.current_members < Fund.max_members
        ).values(current_members=Fund.current_members + 1))
        if reserved.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail="ظرفیت صندوق تکمیل شده است")
    elif member.status == "active" and status == "paused" and fund.status == "draft":
        fund.current_members = max(0, fund.current_members - 1)
    if status == "removed" and member.status != "removed":
        fund.current_members = max(0, fund.current_members - (1 if member.status == "active" else 0))
        member.ended_at = datetime.now(timezone.utc)
        if fund.status == "draft":
            for entry in db.scalars(select(DrawEntry).where(DrawEntry.fund_id == fund_id)):
                db.delete(entry)
    member.status = status
    db.commit()
    return member_output(member)


@router.post("/{fund_id}/draw", response_model=list[DrawOut], status_code=201)
def draw_order(fund_id: int, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = owned_fund(fund_id, owner, db)
    if fund.status != "draft":
        raise HTTPException(status_code=409, detail="قرعه‌کشی فقط پیش از شروع صندوق ممکن است")
    if db.scalar(select(DrawEntry.id).where(DrawEntry.fund_id == fund_id)):
        raise HTTPException(status_code=409, detail="ترتیب قرعه‌کشی قبلاً تعیین شده است")
    members = manager_members(fund_id, db)
    if len(members) < 2:
        raise HTTPException(status_code=400, detail="برای قرعه‌کشی دست‌کم دو عضو فعال لازم است")
    secrets.SystemRandom().shuffle(members)
    now = datetime.now(timezone.utc)
    entries = [DrawEntry(fund_id=fund_id, membership_id=m.id, position=i, drawn_at=now) for i, m in enumerate(members, 1)]
    db.add_all(entries)
    db.commit()
    return [DrawOut(position=e.position, membership_id=e.membership_id, member_name=members[e.position - 1].user.full_name, drawn_at=e.drawn_at) for e in entries]


@router.get("/{fund_id}/draw", response_model=list[DrawOut])
def get_draw(fund_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    fund = db.get(Fund, fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="صندوق پیدا نشد")
    if not user.is_owner and not db.scalar(select(Membership.id).where(Membership.fund_id == fund_id, Membership.user_id == user.id, Membership.status != "removed")):
        raise HTTPException(status_code=403, detail="به این صندوق دسترسی ندارید")
    entries = list(db.scalars(select(DrawEntry).options(joinedload(DrawEntry.membership).joinedload(Membership.user)).where(DrawEntry.fund_id == fund_id).order_by(DrawEntry.position)))
    return [DrawOut(position=e.position, membership_id=e.membership_id, member_name=e.membership.user.full_name, drawn_at=e.drawn_at) for e in entries]


@router.post("/{fund_id}/start", response_model=list[CycleOut])
def start_fund(fund_id: int, data: StartFund, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = owned_fund(fund_id, owner, db)
    if fund.status != "draft":
        raise HTTPException(status_code=409, detail="صندوق قبلاً شروع شده است")
    if not data.confirm_permanent_random_draw:
        raise HTTPException(status_code=400, detail="برای شروع باید دائمی‌بودن ترتیب قرعه‌کشی را تأیید کنید")
    entries = list(db.scalars(select(DrawEntry).options(joinedload(DrawEntry.membership).joinedload(Membership.user)).where(DrawEntry.fund_id == fund_id).order_by(DrawEntry.position)))
    members = manager_members(fund_id, db)
    if len(members) < 2:
        raise HTTPException(status_code=409, detail="برای رسمی‌کردن صندوق دست‌کم دو عضو فعال لازم است")
    if len(entries) != len(members) or {entry.membership_id for entry in entries} != {member.id for member in members}:
        raise HTTPException(status_code=400, detail="ابتدا قرعه‌کشی را انجام دهید و اعضا را نهایی کنید")
    # Once formalized, the actual member count defines the term and draw length.
    fund.max_members = len(members)
    fund.current_members = len(members)
    total = fund.monthly_share * len(members)
    start = fund.start_date
    cycles = []
    for idx, entry in enumerate(entries, 1):
        due_date = add_months(start, idx - 1)
        cycle = Cycle(fund_id=fund.id, number=idx, due_date=due_date, recipient_membership_id=entry.membership_id,
                      gross_amount=total, recipient_share=fund.monthly_share, net_amount=total - fund.monthly_share)
        db.add(cycle)
        db.flush()
        for member in members:
            db.add(Installment(cycle_id=cycle.id, membership_id=member.id, amount=fund.monthly_share,
                               status="paid" if member.id == entry.membership_id else "pending",
                               paid_at=datetime.now(timezone.utc) if member.id == entry.membership_id else None,
                               due_date=due_date + timedelta(days=fund.payment_grace_days)))
        cycles.append((cycle, entry.membership.user.full_name))
    fund.status = "active"
    db.commit()
    return [CycleOut(id=c.id, number=c.number, due_date=c.due_date, recipient_membership_id=c.recipient_membership_id,
                     recipient_name=name, gross_amount=c.gross_amount, recipient_share=c.recipient_share,
                     net_amount=c.net_amount, status=c.status, installments=[]) for c, name in cycles]


def cycle_out(cycle: Cycle) -> CycleOut:
    return CycleOut(id=cycle.id, number=cycle.number, due_date=cycle.due_date,
                    recipient_membership_id=cycle.recipient_membership_id,
                    recipient_name=cycle.recipient.user.full_name, gross_amount=cycle.gross_amount,
                    recipient_share=cycle.recipient_share, net_amount=cycle.net_amount,
                    status=cycle.status, installments=[InstallmentOut.model_validate(x) for x in cycle.installments])


@router.post("/{fund_id}/cycles", response_model=CycleOut, status_code=201)
def add_cycle(fund_id: int, recipient_membership_id: int, due_date: str, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    fund = owned_fund(fund_id, owner, db)
    if fund.status != "active":
        raise HTTPException(status_code=409, detail="صندوق فعال نیست")
    entries = list(db.scalars(select(DrawEntry).where(DrawEntry.fund_id == fund_id).order_by(DrawEntry.position)))
    number = (db.scalar(select(Cycle.number).where(Cycle.fund_id == fund_id).order_by(Cycle.number.desc()).limit(1)) or 0) + 1
    if number > len(entries):
        raise HTTPException(status_code=409, detail="همه نوبت‌های قرعه‌کشی برنامه‌ریزی شده‌اند")
    if entries[number - 1].membership_id != recipient_membership_id:
        raise HTTPException(status_code=400, detail="گیرنده باید مطابق نوبت ثابت قرعه‌کشی باشد")
    from datetime import date
    try:
        due = date.fromisoformat(due_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="تاریخ باید با قالب YYYY-MM-DD باشد")
    members = manager_members(fund_id, db)
    recipient = next((m for m in members if m.id == recipient_membership_id), None)
    if not recipient:
        raise HTTPException(status_code=404, detail="عضو دریافت‌کننده پیدا نشد")
    cycle = Cycle(fund_id=fund.id, number=number, due_date=due, recipient_membership_id=recipient.id,
                  gross_amount=fund.monthly_share * len(members), recipient_share=fund.monthly_share,
                  net_amount=fund.monthly_share * (len(members) - 1))
    db.add(cycle)
    db.flush()
    for m in members:
        db.add(Installment(cycle_id=cycle.id, membership_id=m.id, amount=fund.monthly_share,
                           status="paid" if m.id == recipient.id else "pending",
                           paid_at=datetime.now(timezone.utc) if m.id == recipient.id else None,
                           due_date=due + timedelta(days=fund.payment_grace_days)))
    db.commit()
    db.refresh(cycle)
    cycle = db.scalar(select(Cycle).options(joinedload(Cycle.recipient).joinedload(Membership.user), joinedload(Cycle.installments)).where(Cycle.id == cycle.id))
    return cycle_out(cycle)


@router.get("/{fund_id}/cycles", response_model=list[CycleOut])
def list_cycles(fund_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    fund = db.get(Fund, fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="صندوق پیدا نشد")
    if not user.is_owner and not db.scalar(select(Membership.id).where(Membership.fund_id == fund_id, Membership.user_id == user.id, Membership.status != "removed")):
        raise HTTPException(status_code=403, detail="به این صندوق دسترسی ندارید")
    cycles = db.scalars(select(Cycle).options(joinedload(Cycle.recipient).joinedload(Membership.user), joinedload(Cycle.installments)).where(Cycle.fund_id == fund_id).order_by(Cycle.number)).unique()
    return [cycle_out(c) for c in cycles]


@router.patch("/{fund_id}/cycles/{cycle_id}", response_model=CycleOut)
def update_cycle(fund_id: int, cycle_id: int, data: CycleUpdate, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    owned_fund(fund_id, owner, db)
    cycle = db.scalar(select(Cycle).options(joinedload(Cycle.recipient).joinedload(Membership.user), joinedload(Cycle.installments)).where(
        Cycle.id == cycle_id, Cycle.fund_id == fund_id
    ))
    if not cycle:
        raise HTTPException(status_code=404, detail="وام پیدا نشد")
    cycle.status = data.status
    db.commit()
    return cycle_out(cycle)


@router.get("/{fund_id}/installments", response_model=list[InstallmentOut])
def list_installments(fund_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.is_owner:
        owned_fund(fund_id, user, db)
        membership_id = db.scalar(select(Membership.id).where(
            Membership.fund_id == fund_id, Membership.user_id == user.id
        ))
        if not membership_id:
            return []
    else:
        membership_id = db.scalar(select(Membership.id).where(Membership.fund_id == fund_id, Membership.user_id == user.id, Membership.status != "removed"))
        if not membership_id:
            raise HTTPException(status_code=403, detail="به این صندوق دسترسی ندارید")
    query = select(Installment).join(Cycle).where(
        Cycle.fund_id == fund_id, Installment.membership_id == membership_id
    )
    return list(db.scalars(query.order_by(Installment.due_date)))


@router.patch("/{fund_id}/installments/{installment_id}", response_model=InstallmentOut)
def update_installment(fund_id: int, installment_id: int, data: PaymentUpdate, db: Session = Depends(get_db), owner: User = Depends(owner_user)):
    owned_fund(fund_id, owner, db)
    installment = db.scalar(select(Installment).join(Cycle).where(Installment.id == installment_id, Cycle.fund_id == fund_id))
    if not installment:
        raise HTTPException(status_code=404, detail="قسط پیدا نشد")
    installment.status = data.status
    if data.payment_reference is not None:
        installment.payment_reference = data.payment_reference
    if data.note is not None:
        installment.note = data.note
    installment.paid_at = datetime.now(timezone.utc) if data.status == "paid" else None
    db.commit()
    db.refresh(installment)
    return installment
