# VendorBridge ERP

VendorBridge is a Django-based Procurement & Vendor Management ERP prototype for the hackathon problem statement. It includes role-based workflows for procurement officers, vendors, managers/approvers, and admins.

## Modules

- Authentication and role-based access
- Dashboard analytics
- Vendor management
- RFQ creation and vendor assignment
- Vendor quotation submission
- Quotation comparison with lowest-price highlighting
- Manager approval workflow
- Purchase order generation
- Invoice generation, print, and email action
- Activity logs, notifications, and reports

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Demo users all use password `VendorBridge@123`:

- `admin@vendorbridge.local`
- `officer@vendorbridge.local`
- `manager@vendorbridge.local`
- `vendor@vendorbridge.local`

## MySQL

For MySQL, create a database named `vendorbridge`, copy `.env.example` to `.env`, and set `DB_ENGINE=django.db.backends.mysql` plus your DB credentials. If no `.env` is present, the app uses SQLite for local demo runs.
