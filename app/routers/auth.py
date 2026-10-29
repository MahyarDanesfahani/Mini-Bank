from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import current_user
from app.models import User
from app.schemas import CustomerRegistration, Login, OwnerSetup, ProfileUpdate, Token, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["احراز هویت"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: CustomerRegistration, db: Session = Depends(get_db)):
    email = data.email.lower() if data.email else f"noemail-{data.national_code}@example.com"
    if data.email and db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="این ایمیل قبلاً ثبت شده است")
    if db.scalar(select(User.id).where(User.national_code == data.national_code)):
        raise HTTPException(status_code=409, detail="این کد ملی قبلاً ثبت شده است")
    user = User(
        full_name=data.full_name, email=email, phone=data.phone,
        national_code=data.national_code, birth_date=data.birth_date,
        gender=data.gender, address=data.address, postal_code=data.postal_code,
        occupation=data.occupation, password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/setup-owner", response_model=UserOut, status_code=201)
def setup_owner(data: OwnerSetup, db: Session = Depends(get_db), setup_header: str | None = Header(default=None, alias="X-Setup-Key")):
    if data.setup_key != settings.owner_setup_key or setup_header != settings.owner_setup_key:
        raise HTTPException(status_code=403, detail="کلید راه‌اندازی صحیح نیست")
    if db.scalar(select(User.id).where(User.is_owner.is_(True))) is not None:
        raise HTTPException(status_code=409, detail="مدیر صندوق قبلاً ساخته شده است")
    email = data.email.lower() if data.email else f"noemail-{data.national_code}@example.com"
    existing = db.scalar(select(User).where(User.national_code == data.national_code))
    if existing:
        if data.email and existing.email != email:
            raise HTTPException(status_code=409, detail="کد ملی و ایمیل متعلق به دو حساب متفاوت هستند")
        existing.is_owner = True
        existing.full_name = data.full_name
        existing.phone = data.phone or existing.phone
        existing.password_hash = hash_password(data.password)
        if data.email:
            existing.email = email
        elif existing.email and existing.email.endswith("@no-email.invalid"):
            existing.email = f"noemail-{data.national_code}@example.com"
        db.commit()
        db.refresh(existing)
        return existing
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="این ایمیل قبلاً ثبت شده است")
    user = User(full_name=data.full_name, email=email, national_code=data.national_code, phone=data.phone,
                password_hash=hash_password(data.password), is_owner=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.national_code == data.national_code))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ایمیل یا گذرواژه نادرست است")
    return Token(access_token=create_access_token(user.id))


@router.post("/oauth-token", response_model=Token, include_in_schema=False)
def oauth_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.national_code == form.username))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ایمیل یا گذرواژه نادرست است")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    values = data.model_dump()
    if values["email"]:
        email = values["email"].lower()
        duplicate = db.scalar(select(User.id).where(User.email == email, User.id != user.id))
        if duplicate:
            raise HTTPException(status_code=409, detail="این ایمیل برای حساب دیگری ثبت شده است")
        user.email = email
    else:
        user.email = f"noemail-{user.national_code}@example.com"
    for field in ("full_name", "phone", "birth_date", "gender", "address", "postal_code", "occupation"):
        setattr(user, field, values[field])
    db.commit()
    db.refresh(user)
    return user
