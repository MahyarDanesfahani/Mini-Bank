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


---

# Mini Bank

A Persian, right-to-left, installable PWA for managing family, friends, and group Qard Hasanah funds.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Overview

Mini Bank makes it easier to create and operate community-based interest-free loan funds. Fund owners can create funds, manage members, generate a fixed random draw order, schedule monthly cycles, and track installment payments. Members can join open funds and view their loan and installment schedules.

> **Current status:** This is an initial production-ready foundation. Real banking payments, SMS notifications, and audit-event logging are planned for future releases.

## ✨ Features

- Persian and RTL user interface for authentication and dashboard workflows
- Installable Progressive Web App for mobile and desktop
- Customer registration with national ID and personal information
- One-time setup flow for creating the first fund owner
- Fund creation with monthly share, capacity, start date, and payment grace period
- Open-fund discovery with atomic capacity reservation
- Member management for fund owners
- Random draw order that becomes immutable after confirmation
- Automatic generation of monthly cycles, recipients, and installments
- Installment statuses: pending, paid, late, coordinated, and waived
- Payment reference and note tracking
- Membership history and late-installment statistics
- Interactive OpenAPI documentation at <code>/docs</code>
- SQLite for development and PostgreSQL, Docker, and Caddy for production

## 🧱 Technology Stack

| Area | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| ORM and data | SQLAlchemy 2, SQLite, PostgreSQL |
| Authentication | JWT, Bearer Token, Argon2 |
| Frontend | HTML, CSS, vanilla JavaScript |
| Installability | Web App Manifest, Service Worker, PWA |
| Deployment | Docker Compose, Caddy, automatic HTTPS |

## 📁 Project Structure

~~~text
mini_bank/
├── app/
│   ├── main.py, config.py, database.py
│   ├── models.py, schemas.py, security.py
│   ├── dependencies.py
│   ├── routers/             # auth and funds
│   └── static/              # UI and PWA assets
├── data/                    # SQLite database in development
├── compose.yaml             # app, PostgreSQL, and Caddy
├── Dockerfile
├── Caddyfile
├── requirements.txt
├── .env.example
└── RELEASE_GUIDE_FA.md
~~~

## 🚀 Quick Start

Requirements: Python 3.11+ and pip.

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

After starting the server:

| URL | Purpose |
|---|---|
| <code>http://localhost:8000/</code> | Login and registration |
| <code>http://localhost:8000/setup-owner</code> | Create the first owner |
| <code>http://localhost:8000/dashboard</code> | User dashboard |
| <code>http://localhost:8000/docs</code> | Swagger API documentation |
| <code>http://localhost:8000/health</code> | Health check |

The default SQLite database is created at <code>data/fund.db</code>. Change <code>DATABASE_URL</code> to use another database.

## ⚙️ Environment Configuration

Copy <code>.env.example</code> to <code>.env</code> and replace the secrets:

~~~env
APP_NAME=Mini Bank
DATABASE_URL=sqlite:///./data/fund.db
JWT_SECRET=replace-with-a-long-random-secret-at-least-32-characters
JWT_EXPIRE_MINUTES=60
OWNER_SETUP_KEY=replace-with-a-long-random-key-at-least-24-characters
API_PREFIX=/api/v1
APP_ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:8000"]
~~~

In <code>production</code>, the application rejects default secrets and wildcard CORS (<code>*</code>). Never commit <code>.env</code>.

## 🔄 Fund Workflow

1. Create the first owner at <code>/setup-owner</code>. The setup key must be sent in both the request body and the <code>X-Setup-Key</code> header.
2. Users log in with their national ID and password to receive a Bearer token.
3. The owner creates a fund and adds registered users.
4. Users join draft funds while capacity is available.
5. The owner runs the random draw; the order is stored permanently.
6. The owner confirms the permanent draw order and starts the fund.
7. Monthly cycles and installments are generated automatically, and the owner records their statuses.

Amounts are stored as integers in the smallest currency unit. The default currency is <code>IRT</code>, displayed as toman. For a 10-member fund with a monthly share of 3,000,000 toman, the gross monthly amount is 30,000,000 and the recipient's net amount is 27,000,000.

## 📚 API

The API prefix is <code>/api/v1</code>. Protected user and owner routes require a Bearer token.

| Group | Important routes |
|---|---|
| Authentication | <code>POST /auth/register</code> · <code>POST /auth/token</code> · <code>GET /auth/me</code> |
| Setup | <code>POST /auth/setup-owner</code> |
| Funds | <code>POST /funds</code> · <code>GET /funds</code> · <code>GET /funds/open</code> |
| Membership | <code>POST /funds/{id}/join</code> · <code>POST /funds/{id}/members</code> |
| Draw | <code>POST /funds/{id}/draw</code> · <code>GET /funds/{id}/draw</code> |
| Cycles and installments | <code>POST /funds/{id}/start</code> · <code>GET /funds/{id}/cycles</code> · <code>GET /funds/{id}/installments</code> |
| Installment updates | <code>PATCH /funds/{id}/installments/{installment_id}</code> |

See the complete schemas and responses in [Swagger UI](http://localhost:8000/docs).

## 🐳 Docker Deployment

Set <code>POSTGRES_PASSWORD</code>, <code>DOMAIN</code>, <code>JWT_SECRET</code>, <code>OWNER_SETUP_KEY</code>, and <code>CORS_ORIGINS</code> in <code>.env</code>, then run:

~~~bash
docker compose up -d --build
~~~

The stack includes:

- <code>app</code>: FastAPI on internal port 8000
- <code>db</code>: PostgreSQL 16 with persistent storage
- <code>proxy</code>: Caddy reverse proxy with HTTPS

For DNS, HTTPS, backup, and APK preparation, see [RELEASE_GUIDE_FA.md](RELEASE_GUIDE_FA.md).

## 🔐 Security and Limitations

- Passwords are hashed with Argon2 and never stored in plaintext.
- Keep JWT and setup secrets in a secret manager or a secure <code>.env</code> file.
- Rotate or remove the setup key after creating the owner.
- Use only real application origins in <code>CORS_ORIGINS</code> in production.
- This version records payment status but does not process real banking transactions.

## 🧭 Roadmap

- [ ] Payment gateway integration and transaction reconciliation
- [ ] SMS and push notifications with a background queue
- [ ] Audit events and management reports
- [ ] Database migrations with Alembic
- [ ] Automated API and end-to-end tests
- [ ] Production backup and monitoring

## Contributing

Open an Issue for bug reports or feature requests. For code changes, create a separate branch, add relevant tests, and submit a Pull Request.

## License

No open-source license has been selected yet. Add a LICENSE file with the desired license before public distribution.

<div dir="rtl">Built for simpler, clearer, and more organized group fund management.</div>


