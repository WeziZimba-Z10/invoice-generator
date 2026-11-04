from django.contrib import messages
from django.db.models import ProtectedError
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client


@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, "clients/client_list.html", {"clients": clients})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(
        request, "clients/client_form.html", {"form": form, "title": "Add client"}
    )


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(
        request, "clients/client_form.html", {"form": form, "title": "Edit client"}
    )


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        try:
            client.delete()
        except ProtectedError:
            messages.error(
                request,
                "This client has invoices, so it can't be deleted. "
                "Delete those invoices or move them to another client first.",
            )
        return redirect("client_list")
    return render(request, "clients/client_confirm_delete.html", {"client": client})