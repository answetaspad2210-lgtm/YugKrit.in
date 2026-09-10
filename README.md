# YugKrit — "From Problems to Solutions"

YugKrit is a societal innovation and collaboration platform that connects **Government**
(led by a **Government IT Cell** head-of-platform role), **Universities**, **ULBs/NGOs**
(one merged civic-body dashboard), **Students**, and **Citizens** (phone-verified). It takes
a real-world societal problem, gets it verified, matches it with a university and a student
team, tracks the full solution-development lifecycle (research → design → prototype → testing
→ community validation), and — on verified completion — automatically updates every student's
permanent **Innovation Growth Profile** with achievements and certificates.

This is a complete, working Flask application with a real SQLite database, real
authentication, real file uploads, and a real (rule-based) AI recommendation engine. There are
no placeholder pages, no fake buttons, and no "Coming Soon" screens for core features.

---

## 1. Features

- **Six dashboards on one platform**: Government IT Cell (head of platform), Government,
  University, ULB/NGO (merged), Student, and Citizen — all built on the same authentication
  system, database, and permission model.
- **Government IT Cell** is the platform's head-of-office role: full monitoring, progress
  tracking, validation, and approval rights over every Government department, University,
  ULB/NGO, Student, and Citizen. It reuses the (thoroughly tested) Government dashboard pages
  for org verification / challenge review / project oversight / analytics / audit, plus its
  own citizen account and problem monitoring console.
- **ULB and NGO are merged into one dashboard** with identical features — a single
  registration form (with a category toggle), a single role (`ULB_ADMIN`), and a single set
  of routes/templates. No duplicated code paths.
- **Citizen dashboard** — citizens verify their phone during signup and can post real problems
  and browse/track existing ones immediately after activation.
- **Two ways to log in**: email + password, or mobile number + OTP. Every self-registration
  form (University, ULB/NGO, Student, Citizen) now requires a mobile number and a
  Confirm Password field, so every account can immediately use either login method. There is
  OTP delivery uses Meta WhatsApp Cloud API in real mode; local console mode can be enabled for development.
- **Full challenge lifecycle**: submission (from a ULB/NGO *or* a verified Citizen, with a map
  pin + evidence upload) → AI analysis → government verification → university
  assignment/application → project creation.
- **Team Builder** that links students by `institution_id + registration_number` — a student
  is **never** duplicated, no matter how many projects they join.
- **Milestone workflow**: Research → Design → Prototype → Testing → Community Validation →
  Pilot → Implementation → Final Submission, each trackable with status transitions.
- **Achievement engine**: on verified project completion, achievements, skills, impact, and
  certificate eligibility are derived automatically from database relationships — nothing is
  manually copied.
- **Certificate system** with a public, unauthenticated verification page
  (`/verify/certificate/<id>`).
- **Rule-based AI engine** (`services/ai_service.py`) for challenge categorization, priority
  scoring, skill recommendation, similar-challenge detection, and university matching — works
  out of the box with no external API key. A real LLM/API can be swapped in later.
- **RBAC** with roles and permissions stored in the database and enforced via
  `@role_required(...)` / `@permission_required(...)` decorators — no scattered role checks.
- **Audit log** of every significant action (verifications, assignments, milestone changes,
  project completion).
- **In-app notifications**, file uploads with validation, Leaflet + OpenStreetMap for
  location picking and challenge maps, and Chart.js analytics.
- **Fully responsive** — sidebar collapses to a hamburger menu, tables become cards, forms
  stack to a single column, tested at 375 / 390 / 768 / 1024 / 1440 / 1920px.
- **REST API** (`/api/...`) mirroring the server-rendered routes, ready for a future mobile
  app or JS frontend.
- **13 automated tests** covering auth, RBAC, challenge verification, team/duplicate
  prevention, and the milestone → achievement → certificate pipeline.

---

## 2. Technology Stack

| Layer      | Technology                              |
|------------|------------------------------------------|
| Frontend   | HTML5, CSS3 (custom, no default Bootstrap look), Vanilla JavaScript |
| Backend    | Python 3 + Flask                          |
| Database   | SQLite (dev) — structured so PostgreSQL can be swapped in via `DATABASE_URL` |
| ORM        | SQLAlchemy (via Flask-SQLAlchemy)         |
| Templates  | Jinja2                                    |
| Charts     | Chart.js                                  |
| Maps       | Leaflet.js + OpenStreetMap                |
| Icons      | Font Awesome                              |
| CSS Utility| Bootstrap 5 grid concepts only — all visual styling is custom |

---

## 3. Folder Structure

```
YUGKRIT/
├── app.py                     # Application factory + blueprint registration
├── config.py                  # Environment-driven configuration
├── requirements.txt
├── .env.example
│
├── database/
│   ├── database.py            # SQLAlchemy singleton + init_db()
│   ├── models.py               # All ~35 models (Users, Challenges, Projects, ...)
│   ├── seed.py                 # Roles/permissions + full demo workflow seeder
│   └── schema.sql              # Reference DDL (auto-generated from models)
│
├── routes/                     # One blueprint per area — thin, delegate to services/
│   ├── public_routes.py
│   ├── auth_routes.py
│   ├── government_routes.py    # also serves GOVT_IT_CELL_ADMIN (see GOV_ROLES)
│   ├── itcell_routes.py        # IT Cell overview + citizen verification (IT Cell-only pages)
│   ├── university_routes.py
│   ├── ulb_routes.py           # merged ULB/NGO dashboard
│   ├── student_routes.py
│   ├── citizen_routes.py       # Phone-verified citizens: post/browse problems
│   ├── certificate_routes.py   # public certificate verification
│   ├── notification_routes.py
│   └── api_routes.py           # JSON REST API
│
├── services/                   # All business logic lives here
│   ├── auth_service.py
│   ├── challenge_service.py    # create_challenge(submitter, data, submitter_type="ORG"|"CITIZEN")
│   ├── project_service.py
│   ├── student_service.py      # the critical dedup logic
│   ├── citizen_service.py      # Aadhaar hashing + IT Cell verification
│   ├── otp_service.py          # mobile OTP generation/verification + WhatsApp delivery
│   ├── verification_service.py
│   ├── achievement_service.py
│   ├── certificate_service.py
│   ├── notification_service.py
│   ├── ai_service.py           # rule-based mock AI engine
│   └── audit_service.py
│
├── utils/
│   ├── validators.py            # includes validate_aadhaar(), validate_otp_code(), validate_passwords_match()
│   ├── decorators.py           # @login_required, @role_required, @permission_required
│   ├── helpers.py              # file upload, code generation, API response helpers
│   └── permissions.py          # single source of truth: ROLE -> [permissions]
│
├── templates/
│   ├── base.html                # public site layout
│   ├── shared/                  # dashboard_base.html, sidebars (incl. itcell/citizen), navbar, footer, errors
│   ├── public/, auth/
│   ├── government/, itcell/, university/, ulb/, student/, citizen/
│
├── static/
│   ├── css/  (main.css, dashboard.css, components.css, responsive.css)
│   ├── js/   (main.js, auth.js, dashboard.js, challenges.js, projects.js,
│   │          students.js, notifications.js, charts.js, maps.js)
│   ├── images/
│   └── uploads/                 # created at runtime for uploaded files
│
└── tests/
    ├── conftest.py               # isolated per-test SQLite DB fixture
    ├── test_auth.py
    ├── test_permissions.py
    ├── test_challenges.py
    ├── test_projects.py
    └── test_students.py
```

---

## 4. Installation & Setup

### 4.1 Prerequisites
- Python 3.10+
- pip

### 4.2 Steps

```bash
# 1. Clone / unzip the project, then enter the folder
cd yugkrit

# 2. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment variables
cp .env.example .env
# Edit .env and set a real SECRET_KEY for anything beyond local dev

# 5. Seed the database (creates tables + demo accounts + demo workflow)
python database/seed.py

# 6. Run the application
python app.py
```

The app will be available at **http://127.0.0.1:5000**.

### 4.3 Resetting the database
Delete `yugkrit.db` and re-run `python database/seed.py`.

### 4.4 Moving to PostgreSQL later
Set `DATABASE_URL` in `.env` to a PostgreSQL connection string, e.g.:
```
DATABASE_URL=postgresql://user:password@localhost:5432/yugkrit
```
No model code changes are needed — SQLAlchemy handles the dialect difference.

---

## 5. Demo Accounts (development only)

Seeded by `database/seed.py`. Each account has its own development password, or you can log in
with the phone number via OTP (see section 5a below).

| Role                       | Email                       | Password          | Phone (for OTP login) |
|----------------------------|-----------------------------|-------------------|------------------------|
| Government IT Cell (head)  | itcell@yugkrit.local        | YugKritIT@2026    | 9810000001             |
| Government                 | gov@yugkrit.local           | YugKritGov@2026   | 9810000002             |
| University                 | university@yugkrit.local   | YugKritUni@2026   | 9810000003             |
| Faculty                    | faculty@yugkrit.local      | YugKritFac@2026   | 9810000004             |
| ULB                        | ulb@yugkrit.local           | YugKritULB@2026   | 9810000005             |
| NGO (merged ULB dashboard) | ngo@yugkrit.local           | YugKritNGO@2026   | 9810000006             |
| Student                    | student@college.local       | YugKritStu@2026   | 9810000007             |
| Citizen (Aadhaar-verified) | citizen@yugkrit.local      | YugKritCit@2026   | 9876500000             |

The seed script also creates the full demo workflow from the spec: **"Urban Park Renovation
and Smart Monitoring"** (Lucknow, HIGH priority, 2,400 affected) → verified by government →
assigned to ABC University → project **"Smart Park Monitoring"** created → 5-student team
("Team Parkwatch") added by registration number → Research/Design/Prototype milestones marked
complete, Testing in progress. Advance the remaining milestones from the University dashboard
to see achievements and certificates generate automatically.

It also seeds a **citizen-submitted problem** ("Open drain near Gomti Nagar bus stop") sitting
in `SUBMITTED` status — log in as `itcell@yugkrit.local` and visit
**IT Cell → Citizens → Citizen-Submitted Challenges** (or `/dashboard/it-cell/citizen-challenges`)
to review and verify it, exactly like a ULB/NGO submission.

## 5b. Where platform data is stored and accessed

All application records are stored in the configured SQLAlchemy database. In local development,
the SQLite file is `yugkrit.db` in the project root. For a deployed installation, set
`DATABASE_URL` to PostgreSQL or another SQLAlchemy-supported database; the portal code uses the
same models and relationships.

Use a SQLite viewer such as DB Browser for SQLite to inspect the local file, or query it from a
Python shell:

```bash
python -c "from app import create_app; from database.models import User, Challenge; app=create_app(); ctx=app.app_context(); ctx.push(); print(User.query.count(), Challenge.query.count())"
```

The supported application access points are:

| Data | Portal / route |
|------|----------------|
| Users, roles, organizations and approvals | Government IT Cell: `/dashboard/it-cell/` |
| All challenges, verification, assignment and geo map | Government: `/dashboard/government/challenges`, `/dashboard/government/map` |
| Citizen-submitted problems and identity review | IT Cell: `/dashboard/it-cell/citizen-challenges` |
| University applications, projects, teams and milestones | University: `/dashboard/university/` |
| Student profile, projects, achievements and certificates | Student: `/dashboard/student/` |
| Submitted problems and community validation | ULB/NGO: `/dashboard/ulb/` |
| Citizen's own submissions and status | Citizen: `/dashboard/citizen/` |
| Machine-readable integration data | `/api/challenges`, `/api/challenges/<id>`, `/api/projects` |

The same database row is shared across portals: a citizen or ULB creates a `Challenge`, Government
verifies and assigns it, a University creates the related `Project`, students work through its
`Milestone` records, and the originating civic portal can validate the resulting impact. Status
changes create audit records and portal notifications rather than copying data between databases.

---

## 5a. OTP (Signup and Login)

Every account — the demo accounts above and any newly self-registered University, ULB/NGO,
Student, or Citizen account — uses phone OTP during signup and can log in two ways afterwards:

1. **Email + password** (the original `/auth/login` form), or
2. **Mobile number + OTP**, via `/auth/login/otp`.

Signup data is stored before verification with the new account inactive. The user verifies the
phone at `/auth/signup/otp/verify`; the correct OTP activates the account and logs the user in.

**Real WhatsApp setup:** OTP delivery is integrated with Meta WhatsApp Cloud API. Create a Meta
Business app with WhatsApp enabled, add a WhatsApp Business phone number, create an approved
OTP message template with one body variable (`{{1}}`), and set these values in `.env`:

```dotenv
WHATSAPP_PROVIDER=cloud_api
WHATSAPP_DEFAULT_COUNTRY_CODE=+91
WHATSAPP_PHONE_NUMBER_ID=your-meta-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-meta-access-token
WHATSAPP_TEMPLATE_NAME=yugkrit_otp
WHATSAPP_TEMPLATE_LANGUAGE=en_US
```

Phone numbers already beginning with `+` are sent unchanged. Other numbers are prefixed with
`WHATSAPP_DEFAULT_COUNTRY_CODE`. In local development, set `WHATSAPP_PROVIDER=console` to show
the OTP on-screen without sending a WhatsApp message. Real mode never displays or logs the OTP,
and missing or failed WhatsApp configuration returns a clear error instead of creating a usable
pending code.

OTP security details:
- The 6-digit code is never stored in plain text — only a SHA-256 hash (`OTPCode.code_hash`),
  compared against a hash of whatever the user submits.
- Codes expire after 10 minutes (`otp_service.OTP_EXPIRY_MINUTES`).
- Resending is rate-limited to once every 30 seconds (`OTP_RESEND_COOLDOWN_SECONDS`).
- After 5 incorrect attempts on the same code, it is locked out and a new one must be
  requested.
- Every account's mobile number is unique across the platform (enforced at the database
  level), so OTP login can always resolve to exactly one account.

To test it with a demo account, go to `/auth/login/otp`, enter one of the phone numbers from
the table above (e.g. `9810000001` for the IT Cell), and enter the code received on WhatsApp. With
`WHATSAPP_PROVIDER=console`, the code appears in a development-only flash banner instead.

---

## 6. Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Each test gets its own isolated, temporary SQLite database (see `tests/conftest.py`), so tests
never interfere with each other or with your local `yugkrit.db`.

---

## 7. Key Database Relationships (plain language)

- **Roles are data, not code.** `Role` and `Permission` are database tables, and
  `utils/permissions.py` is the single source of truth for which permissions each role gets
  (`ROLE_PERMISSIONS`) and which dashboard it lands on after login (`ROLE_DASHBOARD`). Current
  roles: `GOVT_IT_CELL_ADMIN`, `GOVERNMENT_ADMIN`, `GOVERNMENT_OFFICER`, `UNIVERSITY_ADMIN`,
  `FACULTY`, `ULB_ADMIN` (also used by NGOs), `STUDENT`, `CITIZEN`.
- **Government IT Cell sits above everyone else.** `GOVT_IT_CELL_ADMIN` is granted every
  monitoring/verification/approval permission in the system (`organization.verify`,
  `challenge.verify`, `challenge.assign`, `project.approve`, `student.view`, `citizen.verify`,
  `audit.view`, ...). Rather than duplicating the Government dashboard's pages, IT Cell users
  are simply added to the `GOV_ROLES` tuple in `routes/government_routes.py`, so they get full
  access to the same (already-tested) challenge/university/ULB-NGO/project/approvals/map/
  analytics/audit pages, with the IT Cell's own sidebar and an extra Citizens section
  (`routes/itcell_routes.py`).
- **ULB and NGO are one dashboard.** `Organization.org_type` is `'ULB'` for both; the `ULB`
  model has a `category` column (`'ULB'` or `'NGO'`) that only changes which fields the
  registration form shows (ULB type vs. NGO registration number). Both use the `ULB_ADMIN`
  role and the exact same routes/templates (`routes/ulb_routes.py`, `templates/ulb/`). A
  pre-merge `NGO` model is kept only for backward compatibility with data created before the
  merge — new registrations never use it.
- **Citizen signup is phone-based.** New profiles are activated by signup OTP and do not require
  an identity-card workflow. Legacy identity columns remain only for compatibility with older
  local databases and are not used by active registration or problem posting.
- **A challenge can be submitted by an organization *or* a citizen.** `Challenge` has both
  `submitted_by_org_id` (nullable) and `submitted_by_citizen_id` (nullable) — exactly one is
  set. `Challenge.submitter_name()` returns the right display name either way, and
  `services/challenge_service.create_challenge(submitter, data, submitter_type="ORG"|"CITIZEN")`
  is the single function both the ULB/NGO dashboard and the Citizen dashboard call.
- **A student is unique per (institution, registration number).** `StudentProfile` has a
  database-level unique constraint on `(institution_id, registration_number)`. The *only*
  correct way to attach a student to a team is
  `services/student_service.find_or_invite_student(...)` — it looks the student up first and
  only creates a new (INVITED) profile if truly not found. This is exercised by
  `tests/test_students.py` and `tests/test_projects.py`.
- **Challenge → Project → Team → Student** is the core chain: a `Challenge` (submitted by a
  ULB/NGO or Citizen, verified by Government/IT Cell) is assigned to a `University`, which
  creates a `Project`, which has one or more `ProjectTeam`s, each with `ProjectTeamMember`s
  pointing at a `StudentProfile`.
- **Project → Milestones → Achievements → Certificates → Growth Profile**: when every
  `Milestone` on a `Project` reaches `COMPLETED`, `project_service.complete_project()` fires
  `achievement_service.generate_achievements_for_project()`, which walks
  `Project → ProjectTeam → ProjectTeamMember → StudentProfile` and creates
  `StudentAchievement` + `Certificate` rows for every team member. The Growth Profile
  (`services/student_service.get_growth_profile`) is **always computed live** from these
  relationships — nothing is duplicated or cached.

---

## 8. API Endpoints (selected)

All responses follow `{"success": true, "data": ...}` or
`{"success": false, "error": {"code": ..., "message": ...}}`.

```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/register

GET    /api/challenges
GET    /api/challenges/<id>
POST   /api/challenges                       (ULB/NGO)
POST   /api/challenges/<id>/verify           (Government)
POST   /api/challenges/<id>/assign           (Government)

GET    /api/universities
GET    /api/ulbs
GET    /api/students/<id>

GET    /api/projects
GET    /api/projects/<id>
POST   /api/milestones/<id>/submit           (Student)
POST   /api/milestones/<id>/approve          (Faculty / University Admin)

GET    /api/achievements/<student_id>
GET    /api/certificates/<certificate_id>
GET    /api/certificates/<certificate_id>/verify

GET    /api/notifications
POST   /api/notifications/<id>/read

GET    /api/analytics
GET    /api/audit
```

---

## 9. Adding a New Dashboard (e.g. Industry, Citizen, Mentor)

The platform was built specifically so this does **not** require touching existing dashboards:

1. **Add the role & permissions** in `utils/permissions.py`:
   ```python
   ROLE_PERMISSIONS["INDUSTRY_ADMIN"] = ["challenge.view", "project.view", ...]
   ROLE_DASHBOARD["INDUSTRY_ADMIN"] = "industry.overview"
   ```
   Re-run `python database/seed.py` to create the role in the database.

2. **Create the blueprint**: `routes/industry_routes.py`
   ```python
   industry_bp = Blueprint("industry", __name__, template_folder="../templates/industry")

   @industry_bp.route("/")
   @role_required("INDUSTRY_ADMIN")
   def overview():
       return render_template("industry/overview.html")
   ```
   Register it in `app.py`:
   ```python
   from routes.industry_routes import industry_bp
   app.register_blueprint(industry_bp, url_prefix="/dashboard/industry")
   ```

3. **Create the templates**: `templates/industry/_base.html` (extends
   `shared/dashboard_base.html`, overrides the `sidebar_menu` block) and
   `templates/industry/overview.html` (extends `industry/_base.html`).

4. **Add static assets** if needed: `static/js/industry.js`, extra CSS rules.

No existing model, route, or template needs to change — `User.role_id` and
`User.organization_id` already generalize to any future role/org type.

## 10. Adding a New Role to an Existing Dashboard
Add the role to `ROLE_PERMISSIONS` in `utils/permissions.py`, add it to the relevant
`@role_required(...)` calls, and re-seed. No schema change is required — `Role` and
`Permission` are already data-driven tables.

## 11. Adding a New Feature (e.g. Messaging thread UI)
The `Message` model already exists in `database/models.py`. To surface it: add a service
function in `services/`, a route in the relevant blueprint, and a template. Follow the
pattern used by Notifications (`services/notification_service.py` →
`routes/notification_routes.py` → `templates/shared/notifications.html`).

---

## 12. Configuration Reference

All configuration lives in `.env` (see `.env.example`):

| Variable       | Purpose                                              |
|----------------|-------------------------------------------------------|
| `SECRET_KEY`   | Flask session signing key — set a real random value in production |
| `DATABASE_URL` | SQLAlchemy connection string (SQLite by default, PostgreSQL-ready) |
| `FLASK_DEBUG`  | `1` for local development, `0` in production          |
| `AI_API_KEY`   | Optional — leave blank to use the built-in rule-based AI engine |

## 13. File Upload Setup
Uploaded files are stored under `static/uploads/<category>/` with randomized filenames
(`secure_filename` + UUID) to prevent path traversal and collisions. Allowed extensions are
configured in `config.py` (`ALLOWED_EXTENSIONS`) and enforced server-side in
`utils/helpers.save_uploaded_file()`. Max upload size is 10MB (`MAX_CONTENT_LENGTH`).

## 14. Troubleshooting

- **`sqlite3.OperationalError: no such table`** — run `python database/seed.py` to create and
  seed the database.
- **Login fails for demo accounts** — re-run the seed script; it's idempotent and safe to
  run multiple times.
- **File upload rejected** — check the extension is in `ALLOWED_EXTENSIONS` in `config.py`
  and the file is under 10MB.
- **Port already in use** — change the port in the `app.run(...)` call at the bottom of
  `app.py`, or stop the process using port 5000.
- **Want to inspect the schema** — see `database/schema.sql` (auto-generated reference DDL)
  or open `yugkrit.db` with any SQLite browser.

---

## 15. Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (never stored in plain text).
- Sessions are signed, HTTP-only, `SameSite=Lax` cookies.
- All role/permission checks go through `utils/decorators.py` — never scattered inline.
- File uploads are validated by extension, given randomized names, and size-limited.
- No secrets are hardcoded — everything sensitive is read from `.env` (which is gitignored;
  only `.env.example` is committed).
- User-facing errors never expose Python stack traces (`app.py` registers 404/403/500
  handlers that render a clean error page).
- **OTP codes are never persisted in full either.** Only a SHA-256 hash is stored, codes expire
  after 10 minutes, resending is rate-limited, and verification is capped at 5 attempts per
  code — see `services/otp_service.py`. There is no real SMS gateway integrated (dev-mode only,
  clearly labelled on-screen); see section 5a.
- **Every mobile number is unique across the platform** (`User.phone`, database-level unique
  constraint), so a single OTP request can only ever resolve to one account.

---

## 16. Demo Accounts Are Development-Only

The eight seeded accounts (`itcell@yugkrit.local`, `gov@yugkrit.local`,
`university@yugkrit.local`, `faculty@yugkrit.local`, `ulb@yugkrit.local`, `ngo@yugkrit.local`,
`student@college.local`, `citizen@yugkrit.local`) are clearly for local demonstration and
evaluation only. Do not seed these into a production database.
