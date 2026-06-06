from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from procurement.models import (
    ActivityLog,
    Approval,
    Invoice,
    Notification,
    Profile,
    PurchaseOrder,
    Quotation,
    QuotationItem,
    RFQ,
    RFQItem,
    RFQVendor,
    Vendor,
)


PASSWORD = "VendorBridge@123"


class Command(BaseCommand):
    help = "Seed VendorBridge with rich demo users, vendors, and full procurement workflow data."

    def handle(self, *args, **options):
        self.stdout.write("🌱  Seeding VendorBridge demo data...")

        # ── Users ─────────────────────────────────────────────────
        def make_user(email, first, last, role, is_staff=False, is_superuser=False, phone="+91 90000 00001"):
            obj, _ = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last},
            )
            obj.email = email
            obj.first_name = first
            obj.last_name = last
            obj.is_staff = is_staff
            obj.is_superuser = is_superuser
            obj.set_password(PASSWORD)
            obj.save()
            obj.profile.role = role
            obj.profile.phone = phone
            obj.profile.country = "India"
            obj.profile.save()
            return obj

        admin   = make_user("admin@vendorbridge.local",   "Aarav",  "Sharma",  Profile.ADMIN,   True, True,  "+91 98001 00001")
        officer = make_user("officer@vendorbridge.local", "Priya",  "Mehta",   Profile.OFFICER, False, False, "+91 98001 00002")
        manager = make_user("manager@vendorbridge.local", "Nisha",  "Kapoor",  Profile.MANAGER, False, False, "+91 98001 00003")
        vendor_user = make_user("vendor@vendorbridge.local", "Rohan", "Joshi", Profile.VENDOR,  False, False, "+91 98001 00004")

        # ── Vendors ────────────────────────────────────────────────
        vendor_data = [
            ("Infra Supplies Pvt Ltd",   "Construction",  "27AABCI1429B2Z0", "Meera Shah",    "infra@example.com",      "+91 98765 43210", "4.7", "Mumbai, Maharashtra"),
            ("TechCore Solutions LTD",   "IT Equipment",  "27AABCT1429B2Z0", "Dev Patel",     "vendor@vendorbridge.local", "+91 98765 43211", "4.4", "Pune, Maharashtra"),
            ("FastLog Transport Co",     "Logistics",     "27AABCF1429B2Z0", "Isha Rao",      "logistics@example.com",  "+91 98765 43212", "3.9", "Delhi, NCR"),
            ("OfficeNeed Furniture Co",  "Furniture",     "27AABCO1429B2Z0", "Kunal Jain",    "office@example.com",     "+91 98765 43213", "4.8", "Ahmedabad, Gujarat"),
            ("MediCare Supplies",        "Healthcare",    "27AABCM1429B2Z0", "Sunita Verma",  "medicare@example.com",   "+91 98765 43214", "4.6", "Hyderabad, Telangana"),
            ("BrandBoost Marketing",     "Marketing",     "27AABCB1429B2Z0", "Arjun Nair",    "brand@example.com",      "+91 98765 43215", "4.2", "Bengaluru, Karnataka"),
            ("CleanPro Maintenance",     "Maintenance",   "27AABCC1429B2Z0", "Divya Singh",   "clean@example.com",      "+91 98765 43216", "4.5", "Chennai, Tamil Nadu"),
            ("DataSafe Cloud Services",  "IT Services",   "27AABCD1429B2Z0", "Vikram Gupta",  "datasafe@example.com",   "+91 98765 43217", "4.3", "Kolkata, West Bengal"),
        ]

        vendor_objs = []
        for name, category, gst, contact, email, phone, rating, address in vendor_data:
            v_user = vendor_user if email == "vendor@vendorbridge.local" else None
            vendor, _ = Vendor.objects.update_or_create(
                email=email,
                defaults={
                    "name": name,
                    "category": category,
                    "gst_number": gst,
                    "contact_name": contact,
                    "phone": phone,
                    "rating": Decimal(rating),
                    "status": Vendor.ACTIVE,
                    "address": address,
                    "user": v_user,
                },
            )
            vendor_objs.append(vendor)

        self.stdout.write(f"  ✓ {len(vendor_objs)} vendors created")

        # ── Helper: build RFQ with items ────────────────────────────
        def make_rfq(title, category, desc, status, created_by, days_until_deadline, items, invited_vendors, days_ago=0):
            rfq, _ = RFQ.objects.update_or_create(
                title=title,
                defaults={
                    "category": category,
                    "description": desc,
                    "deadline": (timezone.now() + timedelta(days=days_until_deadline)).date(),
                    "status": status,
                    "created_by": created_by,
                    "created_at": timezone.now() - timedelta(days=days_ago),
                },
            )
            rfq.items.all().delete()
            rfq.vendor_links.all().delete()
            item_objs = []
            for item_name, qty, unit in items:
                item_objs.append(RFQItem.objects.create(rfq=rfq, item_name=item_name, quantity=qty, unit=unit))
            for vendor in invited_vendors:
                RFQVendor.objects.get_or_create(rfq=rfq, vendor=vendor)
            return rfq, item_objs

        # ── RFQ 1: Draft (unsent, just saved) ──────────────────────
        rfq_draft, _ = make_rfq(
            title="Annual Stationery & Office Supplies",
            category="Stationery",
            desc="Bulk procurement of stationery items for all departments: pens, paper, folders, staplers, etc.",
            status=RFQ.DRAFT,
            created_by=officer,
            days_until_deadline=14,
            items=[("A4 Paper Reams", 200, "PKT"), ("Ballpoint Pens", 500, "NOS"), ("Folders A4", 150, "NOS")],
            invited_vendors=[],
            days_ago=1,
        )

        # ── RFQ 2: Open (sent to vendors, awaiting quotes) ─────────
        rfq_open, _ = make_rfq(
            title="Server Room AC Units",
            category="HVAC",
            desc="Procurement of 5-ton precision air conditioning units for the new server room. Must be energy-star certified.",
            status=RFQ.OPEN,
            created_by=officer,
            days_until_deadline=10,
            items=[("Precision AC Unit 5T", 3, "NOS"), ("Installation Kit", 3, "SET"), ("Extended Warranty", 3, "NOS")],
            invited_vendors=[vendor_objs[0], vendor_objs[2], vendor_objs[6]],
            days_ago=3,
        )

        # ── RFQ 3: Quoted (vendors have responded) ─────────────────
        rfq_quoted, rfq_quoted_items = make_rfq(
            title="Office Furniture Procurement Q2",
            category="Furniture",
            desc="Ergonomic chairs and standing desks for the third-floor expansion. Delivery within 10 days required.",
            status=RFQ.QUOTED,
            created_by=officer,
            days_until_deadline=9,
            items=[("Ergonomic Chair", 25, "NOS"), ("Standing Desk", 10, "NOS"), ("Storage Cabinet", 5, "NOS")],
            invited_vendors=[vendor_objs[0], vendor_objs[1], vendor_objs[3]],
            days_ago=7,
        )
        # Add quotations for rfq_quoted
        for vendor, chair_p, desk_p, cab_p, days in [
            (vendor_objs[0], "3600", "8200", "5500", 12),
            (vendor_objs[1], "3500", "8400", "5200", 14),
            (vendor_objs[3], "3700", "7900", "5800", 10),
        ]:
            q, _ = Quotation.objects.update_or_create(
                rfq=rfq_quoted, vendor=vendor,
                defaults={"delivery_days": days, "gst_percent": Decimal("18"), "notes": "Payment: 20 days net.",
                          "status": Quotation.SUBMITTED, "submitted_at": timezone.now() - timedelta(days=2)},
            )
            q.items.all().delete()
            for item, price in zip(rfq_quoted_items, [chair_p, desk_p, cab_p]):
                QuotationItem.objects.create(quotation=q, rfq_item=item, unit_price=Decimal(price))

        # ── RFQ 4: In Approval ─────────────────────────────────────
        rfq_approval, rfq_approval_items = make_rfq(
            title="IT Hardware Refresh — Laptops",
            category="IT Equipment",
            desc="Replacement of 40 end-of-life laptops for the engineering and finance teams. Minimum i7 12th gen, 16GB RAM.",
            status=RFQ.APPROVAL,
            created_by=officer,
            days_until_deadline=5,
            items=[("Laptop 14\" i7 16GB", 40, "NOS"), ("Laptop Bag", 40, "NOS"), ("USB-C Hub", 40, "NOS")],
            invited_vendors=[vendor_objs[1], vendor_objs[7]],
            days_ago=10,
        )
        for vendor, lap_p, bag_p, hub_p, days in [
            (vendor_objs[1], "72000", "800",  "1200", 7),
            (vendor_objs[7], "68500", "750",  "1100", 9),
        ]:
            q, _ = Quotation.objects.update_or_create(
                rfq=rfq_approval, vendor=vendor,
                defaults={"delivery_days": days, "gst_percent": Decimal("18"), "notes": "Includes 3-year onsite warranty.",
                          "status": Quotation.SUBMITTED, "submitted_at": timezone.now() - timedelta(days=5)},
            )
            q.items.all().delete()
            for item, price in zip(rfq_approval_items, [lap_p, bag_p, hub_p]):
                QuotationItem.objects.create(quotation=q, rfq_item=item, unit_price=Decimal(price))
        # Select cheapest and send to approval
        selected_approval = rfq_approval.quotations.order_by("items__unit_price").first()
        if selected_approval:
            rfq_approval.selected_quotation = selected_approval
            rfq_approval.save()
            selected_approval.status = Quotation.SELECTED
            selected_approval.save()
            Approval.objects.update_or_create(
                rfq=rfq_approval, quotation=selected_approval,
                defaults={"requested_by": officer, "status": Approval.PENDING},
            )
            Notification.objects.get_or_create(
                user=manager,
                title="Approval requested",
                defaults={"message": f"{rfq_approval.title} needs your approval."},
            )

        # ── RFQ 5: Approved (with PO & Invoice) ────────────────────
        rfq_approved, rfq_approved_items = make_rfq(
            title="Cleaning & Housekeeping Services Q1",
            category="Maintenance",
            desc="Annual contract for daily office cleaning, deep cleaning twice monthly, and consumables supply.",
            status=RFQ.APPROVED,
            created_by=officer,
            days_until_deadline=-5,   # past deadline
            items=[("Daily Cleaning (monthly)", 12, "MONTH"), ("Deep Cleaning Session", 24, "NOS"), ("Consumables Kit", 12, "KIT")],
            invited_vendors=[vendor_objs[2], vendor_objs[6]],
            days_ago=20,
        )
        for vendor, svc_p, deep_p, kit_p, days in [
            (vendor_objs[2], "45000", "8000", "3500", 0),
            (vendor_objs[6], "42000", "7500", "3200", 0),
        ]:
            q, _ = Quotation.objects.update_or_create(
                rfq=rfq_approved, vendor=vendor,
                defaults={"delivery_days": days, "gst_percent": Decimal("18"), "notes": "Service SLA: 98% uptime.",
                          "status": Quotation.SUBMITTED, "submitted_at": timezone.now() - timedelta(days=18)},
            )
            q.items.all().delete()
            for item, price in zip(rfq_approved_items, [svc_p, deep_p, kit_p]):
                QuotationItem.objects.create(quotation=q, rfq_item=item, unit_price=Decimal(price))
        selected_approved = rfq_approved.quotations.order_by("items__unit_price").first()
        if selected_approved:
            rfq_approved.selected_quotation = selected_approved
            rfq_approved.save()
            selected_approved.status = Quotation.SELECTED
            selected_approved.save()
            appr, _ = Approval.objects.update_or_create(
                rfq=rfq_approved, quotation=selected_approved,
                defaults={"requested_by": officer, "approver": manager, "status": Approval.APPROVED,
                          "remarks": "Best value. Vendor has good track record.", "decided_at": timezone.now() - timedelta(days=15)},
            )
            po_approved, _ = PurchaseOrder.objects.update_or_create(
                rfq=rfq_approved,
                defaults={"quotation": selected_approved, "po_number": f"PO-{timezone.now():%Y%m%d}-0002", "status": PurchaseOrder.ISSUED,
                          "issued_at": timezone.now() - timedelta(days=14)},
            )
            Invoice.objects.update_or_create(
                purchase_order=po_approved,
                defaults={"invoice_number": f"INV-{timezone.now():%Y%m%d}-0002", "status": Invoice.SENT,
                          "due_date": (timezone.now() + timedelta(days=6)).date(),
                          "sent_at": timezone.now() - timedelta(days=10)},
            )

        # ── RFQ 6: Ordered (fully completed) ───────────────────────
        rfq_ordered, rfq_ordered_items = make_rfq(
            title="Healthcare PPE Kits — Annual Stock",
            category="Healthcare",
            desc="Procurement of safety PPE kits for on-site staff: gloves, masks, sanitisers, safety boots.",
            status=RFQ.ORDERED,
            created_by=officer,
            days_until_deadline=-10,
            items=[("N95 Masks", 1000, "NOS"), ("Nitrile Gloves (box)", 200, "BOX"), ("Hand Sanitiser 5L", 50, "CAN"), ("Safety Boots", 30, "PAIR")],
            invited_vendors=[vendor_objs[4], vendor_objs[0]],
            days_ago=30,
        )
        for vendor, m_p, g_p, s_p, b_p, days in [
            (vendor_objs[4], "25",   "850", "620", "1800", 5),
            (vendor_objs[0], "28",   "900", "590", "1950", 7),
        ]:
            q, _ = Quotation.objects.update_or_create(
                rfq=rfq_ordered, vendor=vendor,
                defaults={"delivery_days": days, "gst_percent": Decimal("5"), "notes": "ISO-certified PPE.",
                          "status": Quotation.SUBMITTED, "submitted_at": timezone.now() - timedelta(days=28)},
            )
            q.items.all().delete()
            for item, price in zip(rfq_ordered_items, [m_p, g_p, s_p, b_p]):
                QuotationItem.objects.create(quotation=q, rfq_item=item, unit_price=Decimal(price))
        selected_ordered = rfq_ordered.quotations.order_by("items__unit_price").first()
        if selected_ordered:
            rfq_ordered.selected_quotation = selected_ordered
            rfq_ordered.save()
            selected_ordered.status = Quotation.SELECTED
            selected_ordered.save()
            appr_ord, _ = Approval.objects.update_or_create(
                rfq=rfq_ordered, quotation=selected_ordered,
                defaults={"requested_by": officer, "approver": manager, "status": Approval.APPROVED,
                          "remarks": "Approved. Delivery confirmed.", "decided_at": timezone.now() - timedelta(days=25)},
            )
            po_ordered, _ = PurchaseOrder.objects.update_or_create(
                rfq=rfq_ordered,
                defaults={"quotation": selected_ordered, "po_number": f"PO-{timezone.now():%Y%m%d}-0001", "status": PurchaseOrder.COMPLETED,
                          "issued_at": timezone.now() - timedelta(days=24)},
            )
            inv_ordered, _ = Invoice.objects.update_or_create(
                purchase_order=po_ordered,
                defaults={"invoice_number": f"INV-{timezone.now():%Y%m%d}-0001", "status": Invoice.PAID,
                          "due_date": (timezone.now() - timedelta(days=4)).date(),
                          "sent_at": timezone.now() - timedelta(days=20)},
            )

        # ── Activity Logs ──────────────────────────────────────────
        log_entries = [
            (admin,   "Demo seeded",        "VendorBridge demo workflow data was fully prepared."),
            (officer, "RFQ created",        "IT Hardware Refresh — Laptops was sent to 2 vendors."),
            (officer, "RFQ created",        "Cleaning & Housekeeping Services Q1 sent to vendors."),
            (officer, "RFQ draft saved",    "'Annual Stationery & Office Supplies' saved as draft."),
            (manager, "Approval approved",  "Cleaning & Housekeeping Services Q1 was approved."),
            (manager, "Approval approved",  "Healthcare PPE Kits — Annual Stock was approved."),
            (admin,   "Invoice emailed",    "INV sent to CleanPro Maintenance."),
            (officer, "Purchase order generated", "PO-0001 issued to MediCare Supplies."),
        ]
        for actor, action, desc in log_entries:
            ActivityLog.objects.get_or_create(actor=actor, action=action, defaults={"description": desc})

        # ── Notifications ──────────────────────────────────────────
        Notification.objects.get_or_create(
            user=manager, title="Approval requested",
            defaults={"message": "IT Hardware Refresh — Laptops needs your approval.", "is_read": False},
        )
        Notification.objects.get_or_create(
            user=officer, title="Invoice overdue soon",
            defaults={"message": "INV for Cleaning Services is due in 6 days.", "is_read": False},
        )
        Notification.objects.get_or_create(
            user=vendor_user, title="New RFQ invitation",
            defaults={"message": "You were invited to quote for IT Hardware Refresh — Laptops.", "is_read": False},
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅  Demo ready! Login with any account below — password: {PASSWORD}\n"
            "   admin@vendorbridge.local    → Admin (full access)\n"
            "   officer@vendorbridge.local  → Procurement Officer\n"
            "   manager@vendorbridge.local  → Manager / Approver\n"
            "   vendor@vendorbridge.local   → Vendor (TechCore Solutions LTD)\n\n"
            "   RFQ pipeline seeded:\n"
            "   • 1 Draft  • 1 Open  • 1 Quoted  • 1 In Approval  • 1 Approved  • 1 Ordered\n"
        ))
