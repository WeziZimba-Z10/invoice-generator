from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import get_profile
from clients.models import Client

from .forms import InvoiceForm, LineItemEditFormSet, LineItemFormSet
from .models import Invoice
from .pdf import build_invoice_pdf


def generate_invoice_number(owner):
    count = Invoice.objects.filter(owner=owner).count() + 1
    while Invoice.objects.filter(owner=owner, number=f"INV-{count:04d}").exists():
        count += 1
    return f"INV-{count:04d}"


def totals_by_currency(invoices):
    totals = {}
    for invoice in invoices:
        current = totals.get(invoice.currency, Decimal("0.00"))
        totals[invoice.currency] = current + invoice.total
    return sorted(totals.items())


@login_required
def dashboard(request):
    today = date.today()
    invoices = list(
        Invoice.objects.filter(owner=request.user)
        .select_related("client")
        .prefetch_related("items")
    )
    outstanding = [i for i in invoices if i.status == Invoice.Status.SENT]
    overdue = [i for i in outstanding if i.due_date < today]
    paid = [i for i in invoices if i.status == Invoice.Status.PAID]
    drafts = [i for i in invoices if i.status == Invoice.Status.DRAFT]

    context = {
        "outstanding_totals": totals_by_currency(outstanding),
        "overdue_totals": totals_by_currency(overdue),
        "paid_totals": totals_by_currency(paid),
        "draft_count": len(drafts),
        "overdue_invoices": sorted(overdue, key=lambda i: i.due_date),
        "recent_invoices": invoices[:5],
        "client_count": Client.objects.filter(owner=request.user).count(),
    }
    return render(request, "dashboard.html", context)


@login_required
def invoice_list(request):
    status = request.GET.get("status", "")
    invoices = (
        Invoice.objects.filter(owner=request.user)
        .select_related("client")
        .prefetch_related("items")
    )
    if status == "overdue":
        invoices = invoices.filter(
            status=Invoice.Status.SENT, due_date__lt=date.today()
        )
    elif status in Invoice.Status.values:
        invoices = invoices.filter(status=status)
    return render(
        request,
        "invoices/invoice_list.html",
        {"invoices": invoices, "current_status": status},
    )


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
            initial={
                "issue_date": today,
                "due_date": today + timedelta(days=30),
                "currency": get_profile(request.user).default_currency,
            },
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


@login_required
def invoice_pdf(request, pk):
    queryset = Invoice.objects.select_related("client", "owner").prefetch_related("items")
    invoice = get_object_or_404(queryset, pk=pk, owner=request.user)
    pdf_bytes = build_invoice_pdf(invoice)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.number}.pdf"'
    return response