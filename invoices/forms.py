from django import forms
from django.forms import inlineformset_factory

from clients.models import Client

from .models import Invoice, LineItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "issue_date", "due_date", "status", "tax_rate", "notes"]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["client"].queryset = Client.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get("issue_date")
        due_date = cleaned_data.get("due_date")
        if issue_date and due_date and due_date < issue_date:
            self.add_error("due_date", "The due date can't be before the issue date.")
        return cleaned_data


LineItemFormSet = inlineformset_factory(
    Invoice,
    LineItem,
    fields=["description", "quantity", "unit_price"],
    extra=2,
    min_num=1,
    validate_min=True,
    can_delete=False,
)