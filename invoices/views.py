from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvoiceForm, LineItemEditFormSet, LineItemFormSet
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


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        formset = LineItemEditFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            return redirect("invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
        formset = LineItemEditFormSet(instance=invoice)
    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "formset": formset, "title": f"Edit invoice {invoice.number}"},
    )


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        invoice.delete()
        return redirect("invoice_list")
    return render(request, "invoices/invoice_confirm_delete.html", {"invoice": invoice})


@login_required
@require_POST
def invoice_set_status(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    new_status = request.POST.get("status")
    if new_status in Invoice.Status.values:
        invoice.status = new_status
        invoice.save(update_fields=["status"])
    return redirect("invoice_detail", pk=invoice.pk)