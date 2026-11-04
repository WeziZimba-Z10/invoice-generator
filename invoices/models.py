from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models

from clients.models import Client


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PAID = "paid", "Paid"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    number = models.CharField(max_length=20)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "number"],
                name="unique_invoice_number_per_owner",
            )
        ]

    def __str__(self):
        return f"Invoice {self.number}"

    @property
    def subtotal(self):
        return sum((item.total for item in self.items.all()), Decimal("0.00"))

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_rate / 100).quantize(Decimal("0.01"))

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    @property
    def is_overdue(self):
        return self.status == self.Status.SENT and self.due_date < date.today()

    @property
    def status_label(self):
        if self.is_overdue:
            return "Overdue"
        return self.get_status_display()


class LineItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("1.00")
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.description

    @property
    def total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))