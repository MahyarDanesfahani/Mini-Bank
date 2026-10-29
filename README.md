# صندوق‌من · Mini Bank

<div dir="rtl">

یک وب‌اپلیکیشن فارسی، راست‌به‌چپ و PWA برای مدیریت صندوق‌های قرض‌الحسنهٔ خانوادگی، دوستانه و گروهی.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

</div>

## معرفی

صندوق‌من ساخت و ادارهٔ صندوق‌های قرض‌الحسنه را ساده و شفاف می‌کند. مدیر می‌تواند صندوق بسازد، اعضا را مدیریت کند، ترتیب دریافت وام را با قرعه‌کشی ثابت مشخص کند و وضعیت اقساط را ثبت کند. اعضا نیز می‌توانند در صندوق‌های باز ثبت‌نام کنند و برنامهٔ دریافت‌ها و اقساط خود را ببینند.

> **وضعیت فعلی:** این پروژه نسخهٔ عملیاتی اولیه است؛ پرداخت بانکی واقعی، ارسال پیامک و ثبت رویدادهای ممیزی هنوز پیاده‌سازی نشده‌اند.

## ✨ قابلیت‌ها

- رابط فارسی و راست‌به‌چپ برای ورود، ثبت‌نام و داشبورد
- نصب به‌عنوان PWA روی موبایل و دسکتاپ
- ثبت‌نام با کد ملی و اطلاعات هویتی
- راه‌اندازی اولین مدیر با کلید یک‌بارمصرف
- ساخت صندوق با سهم ماهانه، ظرفیت، تاریخ شروع و مهلت پرداخت
- نمایش صندوق‌های باز و ثبت‌نام اتمیک تا ظرفیت تکمیل نشود
- افزودن، توقف و حذف اعضا توسط مدیر
- قرعه‌کشی تصادفی و غیرقابل‌تغییر پس از نهایی‌شدن
- ساخت خودکار چرخه‌های ماهانه، نوبت دریافت و اقساط
- ثبت وضعیت قسط، شناسهٔ رسید و یادداشت پرداخت
- مشاهدهٔ سابقهٔ عضویت و اقساط دیرکرده
- مستندات تعاملی OpenAPI در <code>/docs</code>
- پشتیبانی از SQLite در توسعه و PostgreSQL، Docker و Caddy در تولید

## 🧱 فناوری‌ها

| بخش | فناوری |
|---|---|
| Backend | Python، FastAPI، Uvicorn |
| ORM و داده | SQLAlchemy 2، SQLite، PostgreSQL |
| احراز هویت | JWT، Bearer Token، Argon2 |
| Frontend | HTML، CSS، JavaScript بدون فریم‌ورک |
| نصب‌پذیری | Web App Manifest، Service Worker، PWA |
| استقرار | Docker Compose، Caddy، HTTPS خودکار |

## 📁 ساختار پروژه

~~~text
mini_bank/
├── app/
│   ├── main.py, config.py, database.py
│   ├── models.py, schemas.py, security.py
│   ├── dependencies.py
│   ├── routers/             # auth و funds
│   └── static/              # رابط کاربری و فایل‌های PWA
├── data/                    # دیتابیس SQLite در توسعه
├── compose.yaml             # app، PostgreSQL و Caddy
├── Dockerfile
├── Caddyfile
├── requirements.txt
├── .env.example
└── RELEASE_GUIDE_FA.md
~~~

## 🚀 راه‌اندازی سریع

پیش‌نیاز: Python 3.11+ و pip.

### Windows

~~~powershell
git clone <YOUR_REPOSITORY_URL>
cd mini_bank
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py -m uvicorn app.main:app --reload
~~~

### Linux/macOS

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
~~~

پس از اجرا:

| نشانی | کاربرد |
|---|---|
| <code>http://localhost:8000/</code> | ورود و ثبت‌نام |
| <code>http://localhost:8000/setup-owner</code> | ساخت اولین مدیر |
| <code>http://localhost:8000/dashboard</code> | داشبورد کاربر |
| <code>http://localhost:8000/docs</code> | Swagger API |
| <code>http://localhost:8000/health</code> | Health check |

دیتابیس پیش‌فرض در <code>data/fund.db</code> ساخته می‌شود و با <code>DATABASE_URL</code> قابل تغییر است.

## ⚙️ تنظیمات

فایل <code>.env.example</code> را به <code>.env</code> تبدیل و secretها را عوض کنید:

~~~env
APP_NAME=صندوق من
DATABASE_URL=sqlite:///./data/fund.db
JWT_SECRET=یک-رشته-تصادفی-طولانی-حداقل-۳۲-کاراکتر
JWT_EXPIRE_MINUTES=60
OWNER_SETUP_KEY=یک-کلید-تصادفی-طولانی-حداقل-۲۴-کاراکتر
API_PREFIX=/api/v1
APP_ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:8000"]
~~~

در <code>production</code>، secretهای پیش‌فرض و CORS باز (<code>*</code>) پذیرفته نمی‌شوند. فایل <code>.env</code> را commit نکنید.

## 🔄 جریان کار صندوق

1. مدیر در <code>/setup-owner</code> ساخته می‌شود؛ کلید باید در بدنه و هدر <code>X-Setup-Key</code> باشد.
2. کاربر با کد ملی و گذرواژه وارد و Bearer Token دریافت می‌کند.
3. مدیر صندوق را می‌سازد و اعضا را اضافه می‌کند.
4. اعضا در صندوق‌های پیش‌نویس دارای ظرفیت خالی ثبت‌نام می‌کنند.
5. مدیر قرعه‌کشی را اجرا می‌کند؛ ترتیب ذخیره و ثابت می‌شود.
6. مدیر با تأیید دائمی‌بودن ترتیب، صندوق را فعال می‌کند.
7. چرخه‌ها و اقساط ماهانه ساخته می‌شوند و مدیر وضعیت آن‌ها را ثبت می‌کند.

مبالغ به‌صورت عدد صحیح در کوچک‌ترین واحد پول ذخیره می‌شوند؛ پیش‌فرض <code>IRT</code> و واحد نمایشی تومان است. در صندوق ۱۰ نفره با سهم ۳٬۰۰۰٬۰۰۰ تومان، مبلغ ناخالص ۳۰٬۰۰۰٬۰۰۰ و دریافتی خالص ۲۷٬۰۰۰٬۰۰۰ تومان است.

## 📚 API

پیشوند مسیرها <code>/api/v1</code> است و مسیرهای مدیریتی و کاربری به Bearer Token نیاز دارند.

| گروه | مسیرهای مهم |
|---|---|
| احراز هویت | <code>POST /auth/register</code> · <code>POST /auth/token</code> · <code>GET /auth/me</code> |
| راه‌اندازی | <code>POST /auth/setup-owner</code> |
| صندوق | <code>POST /funds</code> · <code>GET /funds</code> · <code>GET /funds/open</code> |
| عضویت | <code>POST /funds/{id}/join</code> · <code>POST /funds/{id}/members</code> |
| قرعه‌کشی | <code>POST /funds/{id}/draw</code> · <code>GET /funds/{id}/draw</code> |
| چرخه و قسط | <code>POST /funds/{id}/start</code> · <code>GET /funds/{id}/cycles</code> · <code>GET /funds/{id}/installments</code> |
| تغییر وضعیت قسط | <code>PATCH /funds/{id}/installments/{installment_id}</code> |

برای جزئیات schemaها به [Swagger UI](http://localhost:8000/docs) مراجعه کنید.

## 🐳 استقرار با Docker

مقادیر <code>POSTGRES_PASSWORD</code>، <code>DOMAIN</code>، <code>JWT_SECRET</code>، <code>OWNER_SETUP_KEY</code> و <code>CORS_ORIGINS</code> را در <code>.env</code> تنظیم کنید:

~~~bash
docker compose up -d --build
~~~

سرویس‌ها:

- <code>app</code>: FastAPI روی پورت داخلی ۸۰۰۰
- <code>db</code>: PostgreSQL 16 با volume پایدار
- <code>proxy</code>: Caddy برای reverse proxy و HTTPS

راهنمای کامل انتشار، DNS، HTTPS، بکاپ و آماده‌سازی APK در [RELEASE_GUIDE_FA.md](RELEASE_GUIDE_FA.md) است.

## 🔐 امنیت و محدودیت‌ها

- گذرواژه‌ها با Argon2 هش می‌شوند.
- secretها را در secret manager یا <code>.env</code> امن نگه دارید.
- کلید راه‌اندازی را پس از ساخت مدیر حذف یا تعویض کنید.
- در production فقط originهای واقعی را در <code>CORS_ORIGINS</code> بگذارید.
- این نسخه وضعیت پرداخت را ثبت می‌کند، اما تراکنش بانکی واقعی انجام نمی‌دهد.

## 🧭 نقشه راه

- [ ] درگاه پرداخت و تطبیق تراکنش
- [ ] پیامک و اعلان پوش با صف پس‌زمینه
- [ ] رویدادهای ممیزی و گزارش‌های مدیریتی
- [ ] مهاجرت دیتابیس با Alembic
- [ ] تست خودکار API و end-to-end
- [ ] پشتیبان‌گیری و پایش عملیاتی

## مشارکت

برای گزارش خطا یا پیشنهاد قابلیت، Issue باز کنید. برای تغییرات کدی، شاخهٔ جدا بسازید، تست‌ها را اضافه کنید و Pull Request ارسال کنید.

## مجوز

در حال حاضر مجوز متن‌بازی تعیین نشده است. پیش از انتشار عمومی، فایل LICENSE را با مجوز موردنظر اضافه کنید.

<div dir="rtl">ساخته‌شده برای مدیریت ساده‌تر، شفاف‌تر و منظم‌تر صندوق‌های گروهی.</div>

