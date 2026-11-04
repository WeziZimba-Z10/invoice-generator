from django.urls import path

from . import views

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("new/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_update, name="invoice_update"),
    path("<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),
    path("<int:pk>/status/", views.invoice_set_status, name="invoice_set_status"),
]