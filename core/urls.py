# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # All expense-related URLs (we'll fill in expenses/urls.py next phase)
    path('', include('expenses.urls')),

    # Redirect bare domain to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]