from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ADMIN = "admin"
    OFFICER = "officer"
    MANAGER = "manager"
    VENDOR = "vendor"
    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (OFFICER, "Procurement Officer"),
        (MANAGER, "Manager / Approver"),
        (VENDOR, "Vendor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=OFFICER)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.FileField(upload_to="profiles/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.get_role_display()})"


class Vendor(models.Model):
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"
    STATUS_CHOICES = [(ACTIVE, "Active"), (PENDING, "Pending"), (BLOCKED, "Blocked")]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendor_profile")
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=32)
    contact_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal("4.2"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class RFQ(models.Model):
    DRAFT = "draft"
    OPEN = "open"
    QUOTED = "quoted"
    APPROVAL = "approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (OPEN, "Open"),
        (QUOTED, "Quoted"),
        (APPROVAL, "In Approval"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (ORDERED, "Ordered"),
    ]

    title = models.CharField(max_length=180)
    category = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_rfqs")
    selected_quotation = models.OneToOneField(
        "Quotation", on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_for_rfq"
    )
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return self.title


class RFQItem(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=20, default="NOS")

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"


class RFQVendor(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="vendor_links")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="rfq_links")
    invited_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("rfq", "vendor")


class Quotation(models.Model):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    SELECTED = "selected"
    STATUS_CHOICES = [(DRAFT, "Draft"), (SUBMITTED, "Submitted"), (SELECTED, "Selected")]

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="quotations")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="quotations")
    delivery_days = models.PositiveIntegerField(default=14)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("18.00"))
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("rfq", "vendor")

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def tax_amount(self):
        return (self.subtotal * self.gst_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def grand_total(self):
        return self.subtotal + self.tax_amount

    def __str__(self):
        return f"{self.vendor} - {self.rfq}"


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    rfq_item = models.ForeignKey(RFQItem, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total(self):
        return self.unit_price * self.rfq_item.quantity


class Approval(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [(PENDING, "Pending"), (APPROVED, "Approved"), (REJECTED, "Rejected")]

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="approvals")
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="approvals")
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approval_requests")
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approvals")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)


class PurchaseOrder(models.Model):
    DRAFT = "draft"
    ISSUED = "issued"
    COMPLETED = "completed"
    STATUS_CHOICES = [(DRAFT, "Draft"), (ISSUED, "Issued"), (COMPLETED, "Completed")]

    po_number = models.CharField(max_length=40, unique=True)
    rfq = models.OneToOneField(RFQ, on_delete=models.CASCADE, related_name="purchase_order")
    quotation = models.OneToOneField(Quotation, on_delete=models.CASCADE, related_name="purchase_order")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ISSUED)
    issued_at = models.DateTimeField(default=timezone.now)

    @property
    def amount(self):
        return self.quotation.grand_total


class Invoice(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    STATUS_CHOICES = [(DRAFT, "Draft"), (SENT, "Sent"), (PAID, "Paid"), (OVERDUE, "Overdue")]

    invoice_number = models.CharField(max_length=40, unique=True)
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE, related_name="invoice")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    due_date = models.DateField()
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def amount(self):
        return self.purchase_order.amount


class ActivityLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class OTPVerification(models.Model):
    EMAIL = "email"
    PHONE = "phone"
    TYPE_CHOICES = [(EMAIL, "Email"), (PHONE, "Phone")]

    # Linked to user after creation, or use session key for pre-signup
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="otps")
    # Also store email/phone directly so we can look up before the user record is final
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    otp_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=EMAIL)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP({self.otp_type}) for {self.email or self.phone}"

