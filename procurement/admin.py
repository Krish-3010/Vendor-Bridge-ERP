from django.contrib import admin

from .models import (
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

admin.site.register(Profile)
admin.site.register(Vendor)
admin.site.register(RFQ)
admin.site.register(RFQItem)
admin.site.register(RFQVendor)
admin.site.register(Quotation)
admin.site.register(QuotationItem)
admin.site.register(Approval)
admin.site.register(PurchaseOrder)
admin.site.register(Invoice)
admin.site.register(ActivityLog)
admin.site.register(Notification)
