## 🌉 VendorBridge ERP

**VendorBridge** is a full-featured **Procurement & Vendor Management ERP** built with Django. It digitises the entire procurement lifecycle — from raising a Request for Quotation (RFQ) to generating invoices — with role-based access, real-time notifications, and a premium dark/light UI.

> Built for the hackathon problem statement on Procurement & Vendor Management.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [User Roles & Permissions](#-user-roles--permissions)
- [Complete Procurement Workflow](#-complete-procurement-workflow)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Setup (SQLite — Recommended for Demo)](#quick-setup-sqlite--recommended-for-demo)
  - [MySQL Setup (Optional)](#mysql-setup-optional)
  - [Email Configuration (Optional)](#email-configuration-optional)
- [Demo Accounts](#-demo-accounts)
- [Pages & Modules Explained](#-pages--modules-explained)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Role-Based Access Control** | 4 distinct roles — Admin, Procurement Officer, Manager/Approver, Vendor — each with tailored views and permissions |
| **RFQ Management** | Create RFQs, save as draft, edit drafts, and send to multiple vendors with a single click |
| **Vendor Portal** | Vendors receive RFQ invitations, submit quotations with item-wise pricing, GST, and delivery timelines |
| **Quotation Comparison** | Side-by-side comparison of all vendor bids with lowest-price highlighting and item breakdown |
| **Approval Workflow** | Officer selects best quote → Manager/Admin approves or rejects with remarks |
| **Purchase Order Generation** | Auto-generate POs from approved quotations with unique PO numbers |
| **Invoice Management** | Generate invoices from POs, email them to vendors via SMTP |
| **OTP Email Verification** | New users verify their email with a 6-digit OTP during signup |
| **Dashboard Analytics** | KPIs — active RFQs, pending approvals, monthly PO value, overdue invoices |
| **Activity Logs** | Full audit trail of every action (who did what, when) |
| **Notifications** | In-app notifications for RFQ invitations, approval requests, and more |
| **Reports** | RFQ status distribution, monthly spend charts, vendor ratings, procurement funnel |
| **Dark / Light Mode** | Toggle between themes with preference saved in localStorage |
| **Responsive Design** | Premium glassmorphism UI with Inter font, gradient accents, and smooth animations |

---

## 👥 User Roles & Permissions

| Role | What They Can Do |
|------|-----------------|
| **Admin** | Full access to every feature. Can do everything an Officer and Manager can do — approve/reject, create RFQs, generate POs & invoices, manage vendors. |
| **Procurement Officer** | Creates and manages RFQs, compares vendor quotations, selects quotes and sends to approval, generates POs and invoices. |
| **Manager / Approver** | Reviews quotations awaiting approval, approves or rejects procurement requests with remarks. Also sees all dashboard analytics. |
| **Vendor** | Receives RFQ invitations, submits quotations with item-wise pricing. Can only see RFQs they are invited to. |

---

## 🔄 Complete Procurement Workflow

Here is the end-to-end flow of how a procurement request moves through VendorBridge:

```
Step 1 — CREATE RFQ
   Officer/Admin creates a new RFQ with:
   • Title, category, description, deadline
   • Line items with quantities
   • Can "Save as Draft" (no vendors needed) or "Save & Send to Vendors"
         │
         ▼
Step 2 — VENDOR SUBMITS QUOTATION
   Vendor logs in → sees the RFQ in "Quotations" page → submits:
   • Unit price for each item
   • Delivery timeline (days)
   • GST percentage and notes
   RFQ status changes: Open → Quoted
         │
         ▼
Step 3 — COMPARE & SELECT
   Officer/Admin goes to "Quotations" page → sees "Quoted RFQs — Awaiting Review"
   → clicks "Compare & Select" → sees side-by-side bids with:
   • Lowest price highlighted in green
   • Per-item price breakdown
   • Delivery days, vendor rating
   → clicks "Request Approval" on the best quote
   RFQ status changes: Quoted → In Approval
         │
         ▼
Step 4 — MANAGER APPROVAL
   Manager sees a badge on "Approvals" in sidebar
   → opens Approvals page → sees pending request with amount & vendor
   → adds remarks and clicks "Approve" or "Reject"
   RFQ status changes: In Approval → Approved (or Rejected)
         │
         ▼
Step 5 — GENERATE PURCHASE ORDER
   Officer/Admin goes to "Purchase Orders" page
   → clicks "Generate PO" for the approved request
   → a unique PO number (e.g. PO-20260606-0001) is assigned
   RFQ status changes: Approved → Ordered
         │
         ▼
Step 6 — GENERATE & EMAIL INVOICE
   Officer/Admin goes to "Invoices" page
   → clicks "Generate Invoice" from the PO
   → clicks "Email Invoice" to send it to the vendor's email address
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Django 5.x |
| Database | SQLite (default for demo) / MySQL 8.x (production) |
| Frontend | HTML5, Vanilla CSS (custom design system), Vanilla JavaScript |
| Fonts | Google Fonts — Inter, JetBrains Mono |
| Email | Django SMTP backend (Gmail, Outlook, etc.) or console backend for dev |
| Auth | Django built-in auth + custom OTP verification |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10 or higher** installed
- **pip** (comes with Python)
- **Git** (to clone the repository)

### Quick Setup (SQLite — Recommended for Demo)

No database server needed — SQLite works out of the box.

**macOS / Linux:**
```bash
# 1. Clone the repository
git clone https://github.com/Krish-3010/Vendor-Bridge-ERP.git
cd Vendor-Bridge-ERP

# 2. Create a virtual environment and activate it
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Load demo data (creates users, vendors, RFQs at every stage)
python manage.py seed_demo

# 6. Start the development server
python manage.py runserver
```

**Windows (PowerShell):**
```powershell
# 1. Clone the repository
git clone https://github.com/Krish-3010/Vendor-Bridge-ERP.git
cd Vendor-Bridge-ERP

# 2. Create a virtual environment and activate it
python -m venv venv
.\venv\Scripts\Activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Load demo data
python manage.py seed_demo

# 6. Start the development server
python manage.py runserver
```

**Open your browser** and go to: **http://127.0.0.1:8000**

---

### MySQL Setup (Optional)

If you prefer MySQL over SQLite:

1. Create a MySQL database:
   ```sql
   CREATE DATABASE vendorbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your MySQL credentials:
   ```env
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=vendorbridge
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

4. Run migrations and seed:
   ```bash
   python manage.py migrate
   python manage.py seed_demo
   python manage.py runserver
   ```

> **Note:** If no `.env` file is present, the app automatically uses SQLite — no configuration needed.

---

### Email Configuration (Optional)

By default, OTP codes and invoice emails are **printed to the terminal console** (no real emails sent). This is perfect for development.

To send real emails (e.g., via Gmail):

1. Edit your `.env` file:
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   ```

2. For Gmail, you'll need an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password).

> **Tip:** Without email configured, check your terminal output for OTP codes during signup.

---

## 🔑 Demo Accounts

After running `python manage.py seed_demo`, these accounts are ready to use:

| Role | Email | Password |
|------|-------|----------|
| 🔴 **Admin** (Full Access) | `admin@vendorbridge.local` | `VendorBridge@123` |
| 🟢 **Procurement Officer** | `officer@vendorbridge.local` | `VendorBridge@123` |
| 🔵 **Manager / Approver** | `manager@vendorbridge.local` | `VendorBridge@123` |
| 🟡 **Vendor** (TechCore Solutions) | `vendor@vendorbridge.local` | `VendorBridge@123` |

### What the Demo Data Includes

The seed command creates a fully populated system:

| Data | Count | Details |
|------|-------|---------|
| **Vendors** | 8 | Across categories: Construction, IT, Logistics, Furniture, Healthcare, Marketing, Maintenance, IT Services |
| **RFQs** | 6 | One at each pipeline stage — Draft, Open, Quoted, In Approval, Approved, Ordered |
| **Quotations** | Multiple per RFQ | Realistic item-wise pricing from different vendors |
| **Purchase Orders** | 2 | One issued, one completed |
| **Invoices** | 2 | One sent, one paid |
| **Activity Logs** | 8+ | Audit trail entries for key actions |
| **Notifications** | 3+ | Pending alerts for manager and vendor |

### Suggested Test Flow

1. **Login as Officer** (`officer@vendorbridge.local`) — explore the dashboard, RFQs, and try creating a new RFQ
2. **Login as Vendor** (`vendor@vendorbridge.local`) — go to Quotations → submit a quote for an open RFQ
3. **Login as Officer** again — go to Quotations → you'll see the newly quoted RFQ → click Compare & Select → click "Request Approval"
4. **Login as Manager** (`manager@vendorbridge.local`) — see the approval badge in sidebar → Approvals → Approve or Reject
5. **Login as Admin** (`admin@vendorbridge.local`) — full access, try generating POs and invoices

---

## 📄 Pages & Modules Explained

### 🏠 Dashboard (`/`)
The landing page after login. Shows 4 KPI cards:
- **Active RFQs** — requests currently in the pipeline
- **Pending Approvals** — how many manager decisions are waiting
- **Monthly PO Value** — total value of purchase orders this month
- **Overdue Invoices** — bills past their due date

Also shows recent purchase orders, recent invoices, and a workflow summary.

---

### 👥 Vendors (`/vendors/`)
Register and manage vendor companies. Each vendor has:
- Company name, category, GST number
- Contact person, email, phone
- Rating (out of 5) and status (Active / Pending / Blocked)

Search by name or GST number. Filter by status.

---

### 📋 RFQs (`/rfqs/`)
The Request for Quotation hub. Features:
- **Create RFQ** — fill in title, category, deadline, description, line items, and quantities
- **Save as Draft** — save without selecting vendors; come back later to edit and send
- **Save & Send to Vendors** — immediately notifies selected vendors
- **Status Filter Chips** — filter by Draft / Open / Quoted / In Approval / Approved / Ordered
- **Edit & Send** button on draft RFQs to continue where you left off

---

### 💰 Quotations (`/quotations/`)
Different views per role:

**Vendor View:**
- "RFQs Awaiting Your Quotation" — assigned RFQs you haven't quoted yet
- "My Submitted Quotations" — your past bids with status tracking

**Officer / Manager / Admin View:**
- "Quoted RFQs — Awaiting Review" — RFQs with received vendor bids, with a **Compare & Select** button
- "All Submitted Quotations" — full table of every vendor bid

---

### 📊 Compare & Select (`/rfqs/<id>/compare/`)
Side-by-side vendor bid comparison:
- Best price highlighted in green
- Per-item price breakdown
- Delivery timeline, GST breakdown, vendor rating
- "Request Approval" button sends the selected bid to the Manager

---

### ✅ Approvals (`/approvals/`)
Three stat cards: Pending / Approved / Rejected counts.

Table of all approval requests with:
- RFQ title, vendor name, amount
- Status badge (pending / approved / rejected)
- Remarks field and Approve/Reject buttons (visible only for pending items, and only to Manager/Admin)

---

### 🛒 Purchase Orders (`/purchase-orders/`)
Lists all generated POs. Shows:
- PO number, RFQ title, vendor, amount, status
- "Generate PO" button for newly approved requests

---

### 🧾 Invoices (`/invoices/`)
Lists all invoices with:
- Invoice number, PO number, vendor, amount, due date, status
- "Generate Invoice" from a PO
- "Email Invoice" — sends the invoice details to the vendor's email

---

### 📈 Reports (`/reports/`)
Visual analytics with Chart.js:
- **RFQ Status Distribution** — doughnut chart
- **Monthly Spend Trend** — bar chart
- **Vendor Ratings** — horizontal bar chart
- **Procurement Funnel** — Open → Quoted → Approval → Approved → Ordered

---

### ⚡ Activity Log (`/activity/`)
Chronological audit trail of all system actions:
- Who performed the action
- What they did
- When it happened

Also shows recent notifications for the logged-in user.

---

### 👤 Profile (`/profile/`)
Edit your account details:
- Name, email, phone, country, address
- Profile image upload
- Personal activity history and analytics charts

---

## 📁 Project Structure

```
Vendor-Bridge-ERP/
├── manage.py                 # Django management entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── db.sqlite3                # SQLite database (auto-created)
│
├── vendorbridge/             # Django project settings
│   ├── settings.py           # App configuration (DB, email, static files)
│   ├── urls.py               # Root URL routing
│   └── wsgi.py               # WSGI entry point
│
├── procurement/              # Main application
│   ├── models.py             # Data models (RFQ, Vendor, Quotation, Approval, PO, Invoice, etc.)
│   ├── views.py              # All view logic (CRUD, workflow, role guards)
│   ├── forms.py              # Django forms (RFQ, Quotation, Signup, Profile)
│   ├── urls.py               # App URL patterns
│   ├── context_processors.py # Sidebar nav, notification badges, role context
│   ├── signals.py            # Auto-create Profile on User creation
│   ├── admin.py              # Django admin registrations
│   └── management/
│       └── commands/
│           └── seed_demo.py  # Demo data seeder (8 vendors, 6 RFQs, full pipeline)
│
├── templates/                # HTML templates
│   ├── base.html             # Master layout (sidebar, topbar, theme toggle)
│   ├── dashboard.html        # Dashboard with KPI cards
│   ├── vendors.html          # Vendor list + registration form
│   ├── rfqs.html             # RFQ list with status filters
│   ├── rfq_form.html         # Create/Edit RFQ form (Draft + Send)
│   ├── quotations.html       # Role-aware quotation views
│   ├── quotation_form.html   # Vendor quotation submission form
│   ├── compare.html          # Side-by-side bid comparison
│   ├── approvals.html        # Approval workflow with stat cards
│   ├── purchase_orders.html  # PO list + generation
│   ├── invoices.html         # Invoice list + email action
│   ├── reports.html          # Charts and analytics
│   ├── activity.html         # Audit log + notifications
│   ├── profile.html          # User profile editor
│   └── auth/
│       ├── login.html        # Login page
│       ├── signup.html       # Registration form
│       └── verify_otp.html   # OTP email verification
│
└── static/
    ├── css/
    │   └── app.css           # Complete design system (light/dark, components)
    └── js/
        └── app.js            # Theme toggle, animations, chart initialisation
```

---
