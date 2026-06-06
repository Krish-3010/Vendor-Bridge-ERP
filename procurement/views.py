import json
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, QuotationForm, RFQForm, SignupForm, UserProfileForm, VendorForm
from .models import (
    ActivityLog,
    Approval,
    Invoice,
    Notification,
    OTPVerification,
    Profile,
    PurchaseOrder,
    Quotation,
    QuotationItem,
    RFQ,
    RFQItem,
    RFQVendor,
    Vendor,
)


# ── OTP Helpers ─────────────────────────────────────────────────
def generate_otp():
    """Return a 6-digit OTP string."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp_code, otp_type="email"):
    """Send OTP code to the given email address."""
    expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    try:
        send_mail(
            subject="VendorBridge — Your Verification Code",
            message=(
                f"Your VendorBridge verification code is:\n\n"
                f"  {otp_code}\n\n"
                f"This code expires in {expiry} minutes.\n"
                f"If you did not request this, please ignore this email."
            ),
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


def log(actor, action, description):
    ActivityLog.objects.create(actor=actor, action=action, description=description)


def user_role(user):
    return getattr(getattr(user, "profile", None), "role", Profile.OFFICER)


def report_metrics(user=None):
    total_po_value = sum(po.amount for po in PurchaseOrder.objects.select_related("quotation").all())
    rfq_count = RFQ.objects.count()
    quote_count = Quotation.objects.count()
    invoice_count = Invoice.objects.count()
    vendor_stats = Vendor.objects.annotate(quote_count=Count("quotations")).order_by("-rating")[:6]
    status_counts = {
        "open": RFQ.objects.filter(status=RFQ.OPEN).count(),
        "quoted": RFQ.objects.filter(status=RFQ.QUOTED).count(),
        "approval": RFQ.objects.filter(status=RFQ.APPROVAL).count(),
        "approved": RFQ.objects.filter(status=RFQ.APPROVED).count(),
        "ordered": RFQ.objects.filter(status=RFQ.ORDERED).count(),
    }
    action_count = ActivityLog.objects.filter(actor=user).count() if user else 0

    # Monthly activity data for the last 6 months
    now = timezone.now()
    monthly_labels = []
    monthly_actions = []
    monthly_spend = []
    for i in range(5, -1, -1):
        month = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        label = month.strftime("%b %y")
        monthly_labels.append(label)
        actor_filter = {"actor": user} if user else {}
        monthly_actions.append(
            ActivityLog.objects.filter(
                created_at__year=month.year,
                created_at__month=month.month,
                **actor_filter,
            ).count()
        )
        month_spend = sum(
            po.amount for po in PurchaseOrder.objects.filter(
                issued_at__year=month.year,
                issued_at__month=month.month,
            ).select_related("quotation")
        )
        monthly_spend.append(float(month_spend))

    return {
        "total_po_value": total_po_value,
        "rfq_count": rfq_count,
        "quote_count": quote_count,
        "invoice_count": invoice_count,
        "vendor_stats": vendor_stats,
        "status_counts": status_counts,
        "action_count": action_count,
        "monthly_labels": monthly_labels,
        "monthly_actions": monthly_actions,
        "monthly_spend": monthly_spend,
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "auth/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Store form data in session — create user ONLY after OTP verified
        expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
        otp_code = generate_otp()
        email = form.cleaned_data["email"]
        phone = form.cleaned_data["phone"]

        # Persist pending signup data in session
        request.session["pending_signup"] = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "email": email,
            "phone": phone,
            "role": form.cleaned_data["role"],
            "country": form.cleaned_data.get("country", ""),
            "address": form.cleaned_data.get("address", ""),
            "password": form.cleaned_data["password1"],
        }

        # Save OTP to DB (keyed by email, no user yet)
        OTPVerification.objects.filter(email=email, is_verified=False).delete()
        OTPVerification.objects.create(
            email=email,
            phone=phone,
            otp_type=OTPVerification.EMAIL,
            code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=expiry),
        )

        # Send OTP — falls back to console in dev
        ok, err = send_otp_email(email, otp_code)
        if not ok:
            messages.warning(
                request,
                f"Could not send OTP email ({err}). In development, check the console for your OTP code.",
            )

        return redirect("verify_otp")

    return render(request, "auth/signup.html", {"form": form})


def verify_otp(request):
    """Show the OTP entry form and handle verification."""
    pending = request.session.get("pending_signup")
    if not pending:
        return redirect("signup")

    email = pending["email"]
    error = None
    resent = False

    if request.method == "POST":
        action = request.POST.get("action", "verify")

        if action == "resend":
            expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
            otp_code = generate_otp()
            OTPVerification.objects.filter(email=email, is_verified=False).delete()
            OTPVerification.objects.create(
                email=email,
                phone=pending.get("phone", ""),
                otp_type=OTPVerification.EMAIL,
                code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=expiry),
            )
            ok, err = send_otp_email(email, otp_code)
            if ok:
                messages.success(request, "A new OTP has been sent to your email.")
            else:
                messages.warning(request, f"Could not send OTP email ({err}). Check console for code.")
            resent = True

        else:
            entered = request.POST.get("otp_code", "").strip()
            otp_obj = (
                OTPVerification.objects.filter(
                    email=email,
                    otp_type=OTPVerification.EMAIL,
                    is_verified=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not otp_obj:
                error = "No OTP found. Please request a new one."
            elif otp_obj.is_expired():
                error = "OTP has expired. Please request a new one."
            elif otp_obj.code != entered:
                error = "Invalid OTP code. Please try again."
            else:
                # OTP correct — create the user
                otp_obj.is_verified = True
                otp_obj.save()

                user = User.objects.create_user(
                    username=pending["email"],
                    email=pending["email"],
                    password=pending["password"],
                    first_name=pending["first_name"],
                    last_name=pending["last_name"],
                )
                profile = user.profile
                profile.role = pending["role"]
                profile.phone = pending["phone"]
                profile.country = pending["country"]
                profile.address = pending["address"]
                profile.save()

                # Link OTP to the new user
                otp_obj.user = user
                otp_obj.save()

                del request.session["pending_signup"]
                login(request, authenticate(username=user.email, password=pending["password"]))
                messages.success(request, "Email verified! Your VendorBridge workspace is ready.")
                return redirect("dashboard")

    return render(request, "auth/verify_otp.html", {
        "email": email,
        "error": error,
        "resent": resent,
    })


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile(request):
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user, profile=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        log(request.user, "Profile updated", "Profile details were updated.")
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    logs = ActivityLog.objects.filter(actor=request.user).select_related("actor")[:30]
    notifications = request.user.notifications.order_by("-created_at")[:8]
    reports = report_metrics(request.user)

    # Build chart data as JSON strings for the template
    status = reports["status_counts"]
    chart_rfq_status_values = json.dumps([
        status["open"], status["quoted"], status["approval"],
        status["approved"], status["ordered"],
    ])
    chart_activity_labels = json.dumps(reports["monthly_labels"])
    chart_activity_values = json.dumps(reports["monthly_actions"])
    chart_spend_labels = json.dumps(reports["monthly_labels"])
    chart_spend_values = json.dumps(reports["monthly_spend"])

    vendor_labels = json.dumps([v.name for v in reports["vendor_stats"]])
    vendor_ratings = json.dumps([float(v.rating) for v in reports["vendor_stats"]])

    funnel_values = json.dumps([
        status["open"], status["quoted"], status["approval"],
        status["approved"], status["ordered"],
    ])

    return render(
        request,
        "profile.html",
        {
            "form": form,
            "logs": logs,
            "notifications": notifications,
            "reports": reports,
            "chart_rfq_status_values": chart_rfq_status_values,
            "chart_activity_labels": chart_activity_labels,
            "chart_activity_values": chart_activity_values,
            "chart_spend_labels": chart_spend_labels,
            "chart_spend_values": chart_spend_values,
            "vendor_labels": vendor_labels,
            "vendor_ratings": vendor_ratings,
            "funnel_values": funnel_values,
        },
    )


@login_required
def dashboard(request):
    role = user_role(request.user)
    if role == Profile.VENDOR:
        vendor = getattr(request.user, "vendor_profile", None)
        invited = RFQ.objects.filter(vendor_links__vendor=vendor).distinct() if vendor else RFQ.objects.none()
        quotes = Quotation.objects.filter(vendor=vendor) if vendor else Quotation.objects.none()
        pos = PurchaseOrder.objects.filter(quotation__vendor=vendor) if vendor else PurchaseOrder.objects.none()
    else:
        invited = RFQ.objects.all()
        quotes = Quotation.objects.all()
        pos = PurchaseOrder.objects.all()

    stats = {
        "active_rfqs": invited.exclude(status__in=[RFQ.REJECTED, RFQ.ORDERED]).count(),
        "pending_approvals": Approval.objects.filter(status=Approval.PENDING).count(),
        "monthly_po_value": sum(po.amount for po in pos.filter(issued_at__month=timezone.now().month)),
        "overdue_invoices": Invoice.objects.filter(status=Invoice.OVERDUE).count(),
    }
    recent_pos = pos.select_related("quotation__vendor").order_by("-issued_at")[:5]
    recent_invoices = Invoice.objects.select_related("purchase_order__quotation__vendor").order_by("-created_at")[:5]
    workflow_steps = [
        ("Open RFQs", stats["active_rfqs"], "Requests currently collecting quotes or approval."),
        ("Submitted quotes", quotes.count(), "Vendor responses available for comparison."),
        ("Pending approvals", stats["pending_approvals"], "Manager decisions waiting in the queue."),
        ("Invoices", recent_invoices.count(), "Generated bills ready to send or print."),
    ]
    return render(
        request,
        "dashboard.html",
        {
            "stats": stats,
            "recent_pos": recent_pos,
            "recent_invoices": recent_invoices,
            "quotes": quotes[:4],
            "workflow_steps": workflow_steps,
        },
    )


@login_required
def vendors(request):
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    vendor_list = Vendor.objects.all().order_by("name")
    if query:
        vendor_list = vendor_list.filter(name__icontains=query) | vendor_list.filter(gst_number__icontains=query)
    if status:
        vendor_list = vendor_list.filter(status=status)

    form = VendorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        vendor = form.save()
        log(request.user, "Vendor registered", f"{vendor.name} was added to VendorBridge.")
        messages.success(request, "Vendor registered successfully.")
        return redirect("vendors")
    return render(request, "vendors.html", {"vendors": vendor_list, "form": form, "statuses": Vendor.STATUS_CHOICES})


@login_required
def rfqs(request):
    role = user_role(request.user)
    status_filter = request.GET.get("status", "")
    if role == Profile.VENDOR:
        vendor = getattr(request.user, "vendor_profile", None)
        rfq_list = RFQ.objects.filter(vendor_links__vendor=vendor).distinct() if vendor else RFQ.objects.none()
    else:
        rfq_list = RFQ.objects.all()
    if status_filter:
        rfq_list = rfq_list.filter(status=status_filter)
    return render(request, "rfqs.html", {"rfqs": rfq_list.order_by("-created_at")})


@login_required
def create_rfq(request):
    form = RFQForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        is_draft = "save_draft" in request.POST
        rfq = form.save(commit=False)
        rfq.created_by = request.user

        if is_draft:
            rfq.status = RFQ.DRAFT
            rfq.save()
            # Save items if provided
            item_names = [line.strip() for line in form.cleaned_data["item_names"].splitlines() if line.strip()]
            quantities = [line.strip() for line in form.cleaned_data["quantities"].splitlines() if line.strip()]
            for index, name in enumerate(item_names):
                qty = int(quantities[index]) if index < len(quantities) and quantities[index].isdigit() else 1
                RFQItem.objects.create(rfq=rfq, item_name=name, quantity=qty)
            log(request.user, "RFQ draft saved", f"'{rfq.title}' was saved as a draft.")
            messages.success(request, f"Draft '{rfq.title}' saved. You can send it to vendors later from the RFQ list.")
            return redirect("rfqs")
        else:
            # Sending to vendors — vendors are required
            vendors = form.cleaned_data.get("vendors")
            if not vendors:
                form.add_error("vendors", "Please select at least one vendor to send the RFQ.")
                return render(request, "rfq_form.html", {"form": form})
            rfq.status = RFQ.OPEN
            rfq.save()
            item_names = [line.strip() for line in form.cleaned_data["item_names"].splitlines() if line.strip()]
            quantities = [line.strip() for line in form.cleaned_data["quantities"].splitlines() if line.strip()]
            for index, name in enumerate(item_names):
                qty = int(quantities[index]) if index < len(quantities) and quantities[index].isdigit() else 1
                RFQItem.objects.create(rfq=rfq, item_name=name, quantity=qty)
            for vendor in vendors:
                RFQVendor.objects.create(rfq=rfq, vendor=vendor)
                if vendor.user:
                    Notification.objects.create(
                        user=vendor.user,
                        title="New RFQ invitation",
                        message=f"You were invited to quote for {rfq.title}.",
                    )
            log(request.user, "RFQ created", f"{rfq.title} was sent to {vendors.count()} vendors.")
            messages.success(request, "RFQ saved and sent to assigned vendors.")
            return redirect("rfqs")
    return render(request, "rfq_form.html", {"form": form})


@login_required
def edit_rfq(request, pk):
    """Allow editing a draft RFQ and optionally sending it to vendors."""
    rfq = get_object_or_404(RFQ, pk=pk, created_by=request.user, status=RFQ.DRAFT)
    # Pre-populate item_names and quantities from existing items
    existing_items = list(rfq.items.all())
    initial = {
        "title": rfq.title,
        "category": rfq.category,
        "deadline": rfq.deadline,
        "description": rfq.description,
        "item_names": "\n".join(i.item_name for i in existing_items),
        "quantities": "\n".join(str(i.quantity) for i in existing_items),
        "vendors": rfq.vendor_links.values_list("vendor_id", flat=True),
    }
    form = RFQForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        is_draft = "save_draft" in request.POST
        rfq.title = form.cleaned_data["title"]
        rfq.category = form.cleaned_data["category"]
        rfq.deadline = form.cleaned_data["deadline"]
        rfq.description = form.cleaned_data["description"]
        # Rebuild items
        rfq.items.all().delete()
        rfq.vendor_links.all().delete()
        item_names = [line.strip() for line in form.cleaned_data["item_names"].splitlines() if line.strip()]
        quantities = [line.strip() for line in form.cleaned_data["quantities"].splitlines() if line.strip()]
        for index, name in enumerate(item_names):
            qty = int(quantities[index]) if index < len(quantities) and quantities[index].isdigit() else 1
            RFQItem.objects.create(rfq=rfq, item_name=name, quantity=qty)
        if is_draft:
            rfq.status = RFQ.DRAFT
            rfq.save()
            log(request.user, "RFQ draft updated", f"'{rfq.title}' draft was updated.")
            messages.success(request, f"Draft '{rfq.title}' updated.")
            return redirect("rfqs")
        else:
            vendors = form.cleaned_data.get("vendors")
            if not vendors:
                form.add_error("vendors", "Please select at least one vendor to send the RFQ.")
                return render(request, "rfq_form.html", {"form": form, "rfq": rfq})
            rfq.status = RFQ.OPEN
            rfq.save()
            for vendor in vendors:
                RFQVendor.objects.create(rfq=rfq, vendor=vendor)
                if vendor.user:
                    Notification.objects.create(
                        user=vendor.user,
                        title="New RFQ invitation",
                        message=f"You were invited to quote for {rfq.title}.",
                    )
            log(request.user, "Draft RFQ sent", f"'{rfq.title}' was sent to {vendors.count()} vendors.")
            messages.success(request, f"RFQ '{rfq.title}' sent to vendors!")
            return redirect("rfqs")
    return render(request, "rfq_form.html", {"form": form, "rfq": rfq})


@login_required
def quotations(request):
    role = user_role(request.user)
    if role == Profile.VENDOR:
        vendor = getattr(request.user, "vendor_profile", None)
        rfqs_to_quote = RFQ.objects.filter(
            vendor_links__vendor=vendor, status__in=[RFQ.OPEN, RFQ.QUOTED]
        ).distinct() if vendor else RFQ.objects.none()
        quotes = Quotation.objects.filter(vendor=vendor) if vendor else Quotation.objects.none()
        rfqs_to_review = RFQ.objects.none()
    else:
        rfqs_to_quote = RFQ.objects.none()   # non-vendors don't submit quotes
        quotes = Quotation.objects.select_related("rfq", "vendor").all()
        # RFQs that have received quotes but haven't been sent to approval yet
        rfqs_to_review = RFQ.objects.filter(
            status=RFQ.QUOTED
        ).prefetch_related("quotations", "quotations__vendor").order_by("-created_at")
    return render(request, "quotations.html", {
        "rfqs": rfqs_to_quote,
        "quotations": quotes,
        "rfqs_to_review": rfqs_to_review,
        "role": role,
    })


@login_required
def submit_quotation(request, rfq_id):
    rfq = get_object_or_404(RFQ, pk=rfq_id)
    vendor = getattr(request.user, "vendor_profile", None)
    if not vendor:
        messages.error(request, "Only vendor users can submit quotations.")
        return redirect("quotations")
    quotation, _ = Quotation.objects.get_or_create(rfq=rfq, vendor=vendor)
    form = QuotationForm(request.POST or None, instance=quotation)
    if request.method == "POST" and form.is_valid():
        quotation = form.save(commit=False)
        quotation.status = Quotation.SUBMITTED
        quotation.submitted_at = timezone.now()
        quotation.save()
        quotation.items.all().delete()
        prices = [p.strip() for p in form.cleaned_data["unit_prices"].splitlines() if p.strip()]
        for index, item in enumerate(rfq.items.all()):
            price = Decimal(prices[index]) if index < len(prices) else Decimal("0")
            QuotationItem.objects.create(quotation=quotation, rfq_item=item, unit_price=price)
        rfq.status = RFQ.QUOTED
        rfq.save()
        log(request.user, "Quotation submitted", f"{vendor.name} quoted {quotation.grand_total} for {rfq.title}.")
        messages.success(request, "Quotation submitted successfully.")
        return redirect("quotations")
    return render(request, "quotation_form.html", {"form": form, "rfq": rfq, "quotation": quotation})


@login_required
def compare_rfq(request, pk):
    rfq = get_object_or_404(RFQ, pk=pk)
    quotations = list(rfq.quotations.filter(status__in=[Quotation.SUBMITTED, Quotation.SELECTED]).select_related("vendor"))
    lowest = min([q.grand_total for q in quotations], default=None)
    if request.method == "POST":
        quote = get_object_or_404(Quotation, pk=request.POST.get("quotation_id"), rfq=rfq)
        Approval.objects.get_or_create(rfq=rfq, quotation=quote, defaults={"requested_by": request.user})
        rfq.selected_quotation = quote
        rfq.status = RFQ.APPROVAL
        rfq.save()
        quote.status = Quotation.SELECTED
        quote.save()
        for manager in User.objects.filter(profile__role=Profile.MANAGER):
            Notification.objects.create(user=manager, title="Approval requested", message=f"{rfq.title} needs approval.")
        log(request.user, "Approval requested", f"{quote.vendor.name} was selected for {rfq.title}.")
        messages.success(request, "Approval workflow initiated.")
        return redirect("approvals")
    return render(request, "compare.html", {"rfq": rfq, "quotations": quotations, "lowest": lowest})


@login_required
def approvals(request):
    approval_list = Approval.objects.select_related("rfq", "quotation__vendor").order_by("-created_at")
    return render(request, "approvals.html", {
        "approvals": approval_list,
        "pending_count":  approval_list.filter(status=Approval.PENDING).count(),
        "approved_count": approval_list.filter(status=Approval.APPROVED).count(),
        "rejected_count": approval_list.filter(status=Approval.REJECTED).count(),
    })


@login_required
def decide_approval(request, approval_id, decision):
    role = user_role(request.user)
    if role not in (Profile.MANAGER, Profile.ADMIN):
        messages.error(request, "Only managers and admins can approve or reject procurement requests.")
        return redirect("approvals")
    approval = get_object_or_404(Approval, pk=approval_id)
    approval.status = Approval.APPROVED if decision == "approve" else Approval.REJECTED
    approval.approver = request.user
    approval.remarks = request.POST.get("remarks", "")
    approval.decided_at = timezone.now()
    approval.save()
    approval.rfq.status = RFQ.APPROVED if approval.status == Approval.APPROVED else RFQ.REJECTED
    approval.rfq.save()
    log(request.user, f"Approval {approval.status}", f"{approval.rfq.title} was {approval.status}.")
    messages.success(request, f"Procurement request {approval.status}.")
    return redirect("approvals")


@login_required
def purchase_orders(request):
    pos = PurchaseOrder.objects.select_related("rfq", "quotation__vendor").order_by("-issued_at")
    approved_without_po = Approval.objects.filter(status=Approval.APPROVED, quotation__purchase_order__isnull=True)
    return render(request, "purchase_orders.html", {"purchase_orders": pos, "approved_without_po": approved_without_po})


@login_required
def generate_po(request, approval_id):
    role = user_role(request.user)
    if role not in (Profile.OFFICER, Profile.MANAGER, Profile.ADMIN):
        messages.error(request, "You do not have permission to generate purchase orders.")
        return redirect("purchase_orders")
    approval = get_object_or_404(Approval, pk=approval_id, status=Approval.APPROVED)

    # Build a unique PO number: date + approval-id + microseconds to avoid
    # collisions with seed data or repeated clicks on the same day.
    now = timezone.now()
    candidate_po_number = f"PO-{now:%Y%m%d}-{approval.id:04d}"
    # If that number is already taken by a *different* RFQ, append microseconds
    if PurchaseOrder.objects.filter(po_number=candidate_po_number).exclude(rfq=approval.rfq).exists():
        candidate_po_number = f"PO-{now:%Y%m%d%H%M%S}-{approval.id:04d}"

    po, created = PurchaseOrder.objects.update_or_create(
        rfq=approval.rfq,
        defaults={
            "quotation": approval.quotation,
            "po_number": candidate_po_number,
        },
    )
    # Ensure po_number is not stale when the row already existed with a different number
    if not created and po.po_number != candidate_po_number:
        # Row existed — keep its original number; don't overwrite
        pass

    approval.rfq.status = RFQ.ORDERED
    approval.rfq.save()
    if created:
        log(request.user, "Purchase order generated", f"{po.po_number} issued to {po.quotation.vendor.name}.")
        messages.success(request, f"Purchase Order {po.po_number} generated successfully.")
    else:
        messages.warning(request, f"A Purchase Order for this RFQ already exists: {po.po_number}.")
    return redirect("purchase_orders")


@login_required
def invoices(request):
    invoice_list = Invoice.objects.select_related("purchase_order__quotation__vendor").order_by("-created_at")
    pos_without_invoice = PurchaseOrder.objects.filter(invoice__isnull=True)
    return render(request, "invoices.html", {"invoices": invoice_list, "pos_without_invoice": pos_without_invoice})


@login_required
def generate_invoice(request, po_id):
    role = user_role(request.user)
    if role not in (Profile.OFFICER, Profile.MANAGER, Profile.ADMIN):
        messages.error(request, "You do not have permission to generate invoices.")
        return redirect("invoices")
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    invoice, created = Invoice.objects.get_or_create(
        purchase_order=po,
        defaults={"invoice_number": f"INV-{timezone.now():%Y%m%d}-{po.id:04d}", "due_date": timezone.now().date() + timedelta(days=20)},
    )
    if created:
        log(request.user, "Invoice generated", f"{invoice.invoice_number} created for {po.po_number}.")
    return redirect("invoices")


@login_required
def email_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    vendor_email = invoice.purchase_order.quotation.vendor.email
    try:
        send_mail(
            subject=f"VendorBridge Invoice {invoice.invoice_number}",
            message=(
                f"Dear {invoice.purchase_order.quotation.vendor.name},\n\n"
                f"Please find below the details for Invoice {invoice.invoice_number}:\n"
                f"  Purchase Order: {invoice.purchase_order.po_number}\n"
                f"  Amount Due: ₹{invoice.amount}\n"
                f"  Due Date: {invoice.due_date}\n\n"
                f"Please arrange payment before the due date.\n\n"
                f"Thank you,\nVendorBridge ERP"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[vendor_email],
            fail_silently=False,
        )
        invoice.status = Invoice.SENT
        invoice.sent_at = timezone.now()
        invoice.save()
        log(request.user, "Invoice emailed", f"{invoice.invoice_number} was emailed to {vendor_email}.")
        messages.success(request, f"Invoice {invoice.invoice_number} sent successfully to {vendor_email}.")
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}. Check your EMAIL settings in .env file.")
    return redirect("invoices")


@login_required
def reports(request):
    rpt = report_metrics(request.user)
    status = rpt["status_counts"]
    chart_rfq_status_values = json.dumps([
        status["open"], status["quoted"], status["approval"],
        status["approved"], status["ordered"],
    ])
    vendor_labels = json.dumps([v.name for v in rpt["vendor_stats"]])
    vendor_ratings = json.dumps([float(v.rating) for v in rpt["vendor_stats"]])
    vendor_quotes = json.dumps([v.quote_count for v in rpt["vendor_stats"]])
    chart_spend_labels = json.dumps(rpt["monthly_labels"])
    chart_spend_values = json.dumps(rpt["monthly_spend"])
    funnel_values = json.dumps([
        status["open"], status["quoted"], status["approval"],
        status["approved"], status["ordered"],
    ])
    return render(request, "reports.html", {
        "reports": rpt,
        "chart_rfq_status_values": chart_rfq_status_values,
        "vendor_labels": vendor_labels,
        "vendor_ratings": vendor_ratings,
        "vendor_quotes": vendor_quotes,
        "chart_spend_labels": chart_spend_labels,
        "chart_spend_values": chart_spend_values,
        "funnel_values": funnel_values,
    })


@login_required
def activity(request):
    logs = ActivityLog.objects.select_related("actor").all()[:40]
    notifications = request.user.notifications.order_by("-created_at")[:10]
    return render(request, "activity.html", {"logs": logs, "notifications": notifications})
