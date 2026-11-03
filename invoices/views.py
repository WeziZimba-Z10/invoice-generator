from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InvoiceForm, LineItemFormSet
from .models import Invoice


def generate_invoice_number(owner):
    count = Invoice.objects.filter(owner=owner).count() + 1
    while Invoice.objects.filter(owner=owner, number=f"INV-{count:04d}").exists():
        count += 1
    return f"INV-{count:04d}"


@login_required
def invoice_list(request):
    invoices = (
        Invoice.objects.filter(owner=request.user)
        .select_related("client")
        .prefetch_related("items")
    )
    return render(request, "invoices/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, pk):
    queryset = Invoice.objects.select_related("client").prefetch_related("items")
    invoice = get_object_or_404(queryset, pk=pk, owner=request.user)
    return render(request, "invoices/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST, user=request.user)
        formset = LineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.owner = request.user
                invoice.number = generate_invoice_number(request.user)
                invoice.save()
                formset.instance = invoice
                formset.save()
            return redirect("invoice_detail", pk=invoice.pk)
    else:
        today = date.today()
        form = InvoiceForm(
            user=request.user,
            initial={"issue_date": today, "due_date": today + timedelta(days=30)},
        )
        formset = LineItemFormSet()
    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "formset": formset, "title": "New invoice"},
    )