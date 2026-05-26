# expenses/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # --- Authentication ---
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # --- Dashboard ---
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # --- Expense CRUD ---
    path('expenses/',                     views.expense_list_view,   name='expense_list'),
    path('expenses/add/',                 views.add_expense_view,    name='add_expense'),
    path('expenses/<int:pk>/edit/',       views.edit_expense_view,   name='edit_expense'),
    path('expenses/<int:pk>/delete/',     views.delete_expense_view, name='delete_expense'),

    # --- Budget ---
    path('budget/set/',                   views.set_budget_view,     name='set_budget'),

    # --- Utilities ---
    path('expenses/export/',              views.export_csv_view,     name='export_csv'),
    path('search/',                       views.search_view,         name='search'),
]