from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["default_currency"]
        labels = {"default_currency": "Default currency for new invoices"}