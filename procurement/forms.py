from decimal import Decimal
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile, Quotation, RFQ, Vendor


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]+", "required": True}))
    country = forms.CharField(max_length=80, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "phone", "country", "address", "password1", "password2"]

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone.isdigit():
            raise forms.ValidationError("Phone number is required and must contain numbers only.")
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1", "")
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
        if not re.match(pattern, password):
            raise forms.ValidationError(
                "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
            )
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password and confirm password do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data["role"]
            profile.phone = self.cleaned_data["phone"]
            profile.country = self.cleaned_data["country"]
            profile.address = self.cleaned_data["address"]
            profile.save()
        return user


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ["name", "category", "gst_number", "contact_name", "email", "phone", "rating", "status", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain numbers only.")
        return phone


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]+", "required": True}))
    country = forms.CharField(max_length=80, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    profile_image = forms.FileField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        super().__init__(*args, **kwargs)
        self.fields["phone"].initial = self.profile.phone
        self.fields["country"].initial = self.profile.country
        self.fields["address"].initial = self.profile.address
        self.fields["profile_image"].initial = self.profile.profile_image

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone.isdigit():
            raise forms.ValidationError("Phone number is required and must contain numbers only.")
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        self.profile.phone = self.cleaned_data["phone"]
        self.profile.country = self.cleaned_data["country"]
        self.profile.address = self.cleaned_data["address"]
        image = self.cleaned_data.get("profile_image")
        if image:
            self.profile.profile_image = image
        if commit:
            self.profile.save()
        return user


class RFQForm(forms.ModelForm):
    vendors = forms.ModelMultipleChoiceField(queryset=Vendor.objects.filter(status=Vendor.ACTIVE), required=True)
    item_names = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), help_text="One item per line")
    quantities = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), help_text="One quantity per line")

    class Meta:
        model = RFQ
        fields = ["title", "category", "deadline", "description", "vendors", "item_names", "quantities"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class QuotationForm(forms.ModelForm):
    unit_prices = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), help_text="One unit price per RFQ item")

    class Meta:
        model = Quotation
        fields = ["delivery_days", "gst_percent", "notes", "unit_prices"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}

    def clean_gst_percent(self):
        return self.cleaned_data["gst_percent"] or Decimal("18.00")
