from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from procurement.models import (
    ActivityLog,
    Approval,
    Invoice,
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
    help = "Seed VendorBridge with demo users and procurement workflow data."

    def handle(self, *args, **options):
        def user(email, first, last, role, is_staff=False, is_superuser=False):
            obj, created = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": first, "last_name": last})
            obj.email = email
            obj.first_name = first
            obj.last_name = last
            obj.is_staff = is_staff
            obj.is_superuser = is_superuser
            obj.set_password(PASSWORD)
            obj.save()
            obj.profile.role = role
            obj.profile.phone = "+91 90000 00000"
            obj.profile.country = "India"
            obj.profile.save()
            return obj

        admin = user("admin@vendorbridge.local", "Aarav", "Admin", Profile.ADMIN, True, True)
        officer = user("officer@vendorbridge.local", "Priya", "Officer", Profile.OFFICER)
        manager = user("manager@vendorbridge.local", "Nisha", "Manager", Profile.MANAGER)
        vendor_user = user("vendor@vendorbridge.local", "Rohan", "Vendor", Profile.VENDOR)

        vendors = [
            ("Infra Supplies Pvt Ltd", "Construction", "27AABCI1429B2Z0", "Meera Shah", "infra@example.com", "4.7"),
            ("TechCore LTD", "IT", "27AABCT1429B2Z0", "Dev Patel", "vendor@vendorbridge.local", "4.4"),
            ("FastLog Transport", "Logistics", "27AABCF1429B2Z0", "Isha Rao", "logistics@example.com", "3.9"),
            ("OfficeNeed Co", "Furniture", "27AABCO1429B2Z0", "Kunal Jain", "office@example.com", "4.8"),
        ]
        vendor_objs = []
        for name, category, gst, contact, email, rating in vendors:
            vendor, _ = Vendor.objects.update_or_create(
                email=email,
                defaults={
                    "name": name,
                    "category": category,
                    "gst_number": gst,
                    "contact_name": contact,
                    "phone": "+91 98765 43210",
                    "rating": Decimal(rating),
                    "status": Vendor.ACTIVE,
                    "address": "Ahmedabad, Gujarat",
                    "user": vendor_user if email == "vendor@vendorbridge.local" else None,
                },
            )
            vendor_objs.append(vendor)

        rfq, _ = RFQ.objects.update_or_create(
            title="Office Furniture Procurement Q2",
            defaults={
                "category": "Furniture",
                "description": "Ergonomic chairs and standing desks for the third floor expansion.",
                "deadline": timezone.now().date() + timedelta(days=9),
                "status": RFQ.QUOTED,
                "created_by": officer,
            },
        )
        rfq.items.all().delete()
        chair = RFQItem.objects.create(rfq=rfq, item_name="Ergonomic chair", quantity=25, unit="NOS")
        desk = RFQItem.objects.create(rfq=rfq, item_name="Standing desk", quantity=10, unit="NOS")
        for vendor in vendor_objs[:3]:
            RFQVendor.objects.get_or_create(rfq=rfq, vendor=vendor)

        for vendor, chair_price, desk_price, days in [
            (vendor_objs[0], "3600", "8200", 12),
            (vendor_objs[1], "3500", "8400", 14),
            (vendor_objs[3], "3700", "7900", 10),
        ]:
            quote, _ = Quotation.objects.update_or_create(
                rfq=rfq,
                vendor=vendor,
                defaults={"delivery_days": days, "gst_percent": Decimal("18"), "notes": "Payment terms: 20 days net.", "status": Quotation.SUBMITTED, "submitted_at": timezone.now()},
            )
            quote.items.all().delete()
            QuotationItem.objects.create(quotation=quote, rfq_item=chair, unit_price=Decimal(chair_price))
            QuotationItem.objects.create(quotation=quote, rfq_item=desk, unit_price=Decimal(desk_price))

        selected = rfq.quotations.order_by("items__unit_price").first()
        if selected:
            rfq.selected_quotation = selected
            rfq.status = RFQ.APPROVED
            rfq.save()
            approval, _ = Approval.objects.update_or_create(
                rfq=rfq,
                quotation=selected,
                defaults={"requested_by": officer, "approver": manager, "status": Approval.APPROVED, "remarks": "Approved based on price and delivery timeline.", "decided_at": timezone.now()},
            )
            po, _ = PurchaseOrder.objects.update_or_create(
                rfq=rfq,
                quotation=selected,
                defaults={"po_number": f"PO-{timezone.now():%Y%m%d}-0001", "status": PurchaseOrder.ISSUED},
            )
            Invoice.objects.update_or_create(
                purchase_order=po,
                defaults={"invoice_number": f"INV-{timezone.now():%Y%m%d}-0001", "status": Invoice.DRAFT, "due_date": timezone.now().date() + timedelta(days=20)},
            )

        ActivityLog.objects.get_or_create(actor=admin, action="Demo seeded", description="VendorBridge demo workflow data was prepared.")
        self.stdout.write(self.style.SUCCESS(f"Demo ready. Password for all users: {PASSWORD}"))
