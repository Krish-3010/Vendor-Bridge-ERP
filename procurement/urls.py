from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("signup/verify/", views.verify_otp, name="verify_otp"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("vendors/", views.vendors, name="vendors"),
    path("rfqs/", views.rfqs, name="rfqs"),
    path("rfqs/create/", views.create_rfq, name="create_rfq"),
    path("rfqs/<int:pk>/compare/", views.compare_rfq, name="compare_rfq"),
    path("quotations/", views.quotations, name="quotations"),
    path("quotations/<int:rfq_id>/submit/", views.submit_quotation, name="submit_quotation"),
    path("approvals/", views.approvals, name="approvals"),
    path("approvals/<int:approval_id>/<str:decision>/", views.decide_approval, name="decide_approval"),
    path("purchase-orders/", views.purchase_orders, name="purchase_orders"),
    path("purchase-orders/<int:approval_id>/generate/", views.generate_po, name="generate_po"),
    path("invoices/", views.invoices, name="invoices"),
    path("invoices/<int:po_id>/generate/", views.generate_invoice, name="generate_invoice"),
    path("invoices/<int:invoice_id>/email/", views.email_invoice, name="email_invoice"),
    path("reports/", views.reports, name="reports"),
    path("activity/", views.activity, name="activity"),
]
