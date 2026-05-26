# expenses/admin.py

from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Customizes how Expenses appear in Django's built-in Admin panel.
    Visit /admin after setup to see this in action.
    """

    # Columns shown in the list view
    list_display  = ('user', 'amount', 'category', 'date', 'description', 'created_at')

    # Clickable filters on the right sidebar
    list_filter   = ('category', 'date', 'user')

    # Fields you can search by
    search_fields = ('description', 'user__username', 'category')

    # Default sort in admin (newest first)
    ordering      = ('-date',)

    # Show 25 items per page
    list_per_page = 25
    
    
    
    # expenses/admin.py
# Add this below the existing ExpenseAdmin class

from .models import Expense, Budget     # update the import line

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display  = ('user', 'amount', 'month', 'year', 'updated_at')
    list_filter   = ('year', 'month', 'user')
    ordering      = ('-year', '-month')