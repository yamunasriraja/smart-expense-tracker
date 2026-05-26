# expenses/models.py

from django.db import models
from django.contrib.auth.models import User


class Expense(models.Model):
    """
    Represents a single expense entry made by a user.
    Each row in the database = one expense transaction.
    """

    # --- Expense Categories ---
    CATEGORY_CHOICES = [
        ('food',          'Food & Dining'),
        ('transport',     'Transport'),
        ('housing',       'Housing & Rent'),
        ('entertainment', 'Entertainment'),
        ('health',        'Health & Medical'),
        ('shopping',      'Shopping'),
        ('education',     'Education'),
        ('utilities',     'Utilities & Bills'),
        ('travel',        'Travel'),
        ('other',         'Other'),
    ]

    # --- Fields (each = one column in the database) ---
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    # ^ Links this expense to a user. If the user is deleted, all their expenses are too.

    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    # ^ Stores money values. max_digits=10 means up to 99,999,999.99

    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    # ^ Stores one of the category strings above

    date        = models.DateField()
    # ^ Stores just the date (no time): 2025-01-15

    description = models.TextField(blank=True, null=True)
    # ^ Optional notes about the expense. blank=True means form can be empty,
    #   null=True means database can store NULL

    created_at  = models.DateTimeField(auto_now_add=True)
    # ^ Automatically set when the expense is first created. Never changes.

    updated_at  = models.DateTimeField(auto_now=True)
    # ^ Automatically updated every time the expense is saved.

    class Meta:
        ordering = ['-date', '-created_at']
        # ^ Default sort: newest date first. The '-' means descending order.
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    def __str__(self):
        # This controls what you see in Django Admin: "Food - ₹500.00 (2025-01-15)"
        return f"{self.get_category_display()} - ₹{self.amount} ({self.date})"

    def get_category_icon(self):
        """Returns a Bootstrap icon name for each category."""
        icons = {
            'food':          'bi-cup-hot',
            'transport':     'bi-car-front',
            'housing':       'bi-house',
            'entertainment': 'bi-controller',
            'health':        'bi-heart-pulse',
            'shopping':      'bi-bag',
            'education':     'bi-book',
            'utilities':     'bi-lightning',
            'travel':        'bi-airplane',
            'other':         'bi-three-dots',
        }
        return icons.get(self.category, 'bi-three-dots')
    
    
    
    
    
# expenses/models.py
# Add this BELOW the existing Expense class

class Budget(models.Model):
    """
    Stores a user's monthly spending limit.

    One Budget row per user per month.
    We use unique_together to enforce this at the database level —
    a user can only have ONE budget for any given year+month combination.
    """

    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    month      = models.IntegerField()    # 1–12
    year       = models.IntegerField()    # e.g. 2025

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'year', 'month')
        # ^ Database-level constraint: one budget per user per month.
        # If you try to create a duplicate, the database raises an IntegrityError.
        ordering = ['-year', '-month']
        verbose_name         = 'Budget'
        verbose_name_plural  = 'Budgets'

    def __str__(self):
        return f"{self.user.username} — ₹{self.amount} ({self.month}/{self.year})"

    @property
    def month_name(self):
        """Returns the full month name, e.g. 'January 2025'."""
        from datetime import date
        return date(self.year, self.month, 1).strftime('%B %Y')    