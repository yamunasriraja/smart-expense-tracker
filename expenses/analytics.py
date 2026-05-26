# expenses/analytics.py
"""
Analytics helper functions for the Smart Expense Tracker dashboard.

All functions take a 'user' argument and return only that user's data.
This file keeps views.py clean and makes logic easy to test and reuse.
"""

from django.db.models     import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from datetime             import date, timedelta
from dateutil.relativedelta import relativedelta
from .models              import Expense


# ------------------------------------------------------------------
# MONTHLY SUMMARY
# ------------------------------------------------------------------

def get_monthly_summary(user, year, month):
    """
    Returns total spending and transaction count for a given month.

    Args:
        user:  the logged-in User object
        year:  integer year  (e.g. 2025)
        month: integer month (e.g. 1–12)

    Returns:
        dict with 'total' (Decimal) and 'count' (int)
    """
    qs = Expense.objects.filter(
        user=user,
        date__year=year,
        date__month=month
    )

    result = qs.aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    return {
        'total': result['total'] or 0,
        'count': result['count'] or 0,
    }


def get_spending_change(this_month_total, last_month_total):
    """
    Calculates the percentage change between this month and last month.

    Returns:
        float: positive = overspending vs last month
               negative = underspending vs last month
               None     = no last month data to compare
    """
    if not last_month_total or last_month_total == 0:
        return None

    change = ((this_month_total - last_month_total) / last_month_total) * 100
    return round(change, 1)


# ------------------------------------------------------------------
# CATEGORY BREAKDOWN (for pie chart)
# ------------------------------------------------------------------

def get_category_breakdown(user, year, month):
    """
    Returns spending per category for a given month, sorted by total descending.

    Returns a list of dicts, e.g.:
    [
        {'category': 'food',      'total': Decimal('3200.00'), 'count': 12},
        {'category': 'transport', 'total': Decimal('1500.00'), 'count':  8},
        ...
    ]
    """
    breakdown = (
        Expense.objects
        .filter(user=user, date__year=year, date__month=month)
        .values('category')                      # GROUP BY category
        .annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        .order_by('-total')                      # Highest spend first
    )

    return list(breakdown)


def get_top_category(category_breakdown):
    """
    Returns the name and total of the highest-spending category.
    Returns None if there's no data.
    """
    if not category_breakdown:
        return None

    top = category_breakdown[0]    # Already sorted descending by total

    # Get the human-readable label from the model's CATEGORY_CHOICES
    category_labels = dict(Expense.CATEGORY_CHOICES)

    return {
        'category': top['category'],
        'label':    category_labels.get(top['category'], top['category'].title()),
        'total':    top['total'],
        'count':    top['count'],
    }


# ------------------------------------------------------------------
# MONTHLY TREND (for line chart — last 6 months)
# ------------------------------------------------------------------

def get_monthly_trend(user, months=6):
    """
    Returns total spending for each of the last N months.
    Always returns exactly N entries, even if some months have ₹0.

    Returns a list of dicts ordered oldest → newest, e.g.:
    [
        {'label': 'Aug 2024', 'total': 4200.00},
        {'label': 'Sep 2024', 'total': 3800.00},
        ...
        {'label': 'Jan 2025', 'total': 5100.00},
    ]
    """
    today      = date.today()
    trend_data = []

    for i in range(months - 1, -1, -1):
        # Work backwards: i=5 = 5 months ago, i=0 = this month
        target_date  = today - relativedelta(months=i)
        target_year  = target_date.year
        target_month = target_date.month

        result = Expense.objects.filter(
            user=user,
            date__year=target_year,
            date__month=target_month
        ).aggregate(total=Sum('amount'))

        trend_data.append({
            'label': target_date.strftime('%b %Y'),   # e.g. "Jan 2025"
            'total': float(result['total'] or 0),
        })

    return trend_data


# ------------------------------------------------------------------
# RECENT TRANSACTIONS
# ------------------------------------------------------------------

def get_recent_transactions(user, limit=6):
    """
    Returns the N most recent expenses for the user.
    Used in the dashboard's "Recent Transactions" feed.
    """
    return (
        Expense.objects
        .filter(user=user)
        .order_by('-date', '-created_at')
        [:limit]
    )


# ------------------------------------------------------------------
# SMART INSIGHTS
# ------------------------------------------------------------------

def get_smart_insights(user, year, month, category_breakdown, this_month_total, last_month_total):
    """
    Generates a list of contextual, human-readable insight messages.
    Each insight is a dict with 'type' (success/warning/info/danger) and 'message'.

    These are shown as colored alert banners on the dashboard.
    """
    insights       = []
    category_labels = dict(Expense.CATEGORY_CHOICES)

    # --- Insight 1: No spending yet this month ---
    if this_month_total == 0:
        insights.append({
            'type':    'info',
            'icon':    'bi-info-circle',
            'message': "You haven't logged any expenses this month yet. Start tracking to see insights!"
        })
        return insights      # Nothing else makes sense without data

    # --- Insight 2: Overspending vs last month ---
    if last_month_total and last_month_total > 0:
        change = get_spending_change(this_month_total, last_month_total)
        if change is not None:
            if change >= 30:
                insights.append({
                    'type':    'danger',
                    'icon':    'bi-exclamation-triangle',
                    'message': f"Your spending is up {change}% compared to last month. "
                               f"Consider reviewing your expenses."
                })
            elif change >= 10:
                insights.append({
                    'type':    'warning',
                    'icon':    'bi-arrow-up-circle',
                    'message': f"Spending is up {change}% vs last month — slightly higher than usual."
                })
            elif change <= -10:
                insights.append({
                    'type':    'success',
                    'icon':    'bi-arrow-down-circle',
                    'message': f"Great job! You're spending {abs(change)}% less than last month. 🎉"
                })

    # --- Insight 3: Top category dominates spending ---
    if category_breakdown:
        top = category_breakdown[0]
        if this_month_total > 0:
            top_pct = (top['total'] / this_month_total) * 100
            top_label = category_labels.get(top['category'], top['category'].title())

            if top_pct >= 50:
                insights.append({
                    'type':    'warning',
                    'icon':    'bi-pie-chart',
                    'message': f"{int(top_pct)}% of your spending this month is on "
                               f"{top_label}. Consider whether that's intentional."
                })
            else:
                insights.append({
                    'type':    'info',
                    'icon':    'bi-bar-chart',
                    'message': f"Your top spending category this month is "
                               f"{top_label} (₹{top['total']:,.2f})."
                })

    # --- Insight 4: Spending pace warning ---
    today      = date.today()
    days_in_month  = (date(today.year, today.month % 12 + 1, 1) - timedelta(days=1)).day if today.month < 12 \
                     else 31
    days_passed    = today.day
    days_remaining = days_in_month - days_passed

    if days_passed > 0 and days_remaining > 0:
        daily_rate       = float(this_month_total) / days_passed
        projected_total  = daily_rate * days_in_month

        if last_month_total and projected_total > float(last_month_total) * 1.25:
            insights.append({
                'type':    'warning',
                'icon':    'bi-calendar-x',
                'message': f"At your current pace, you're on track to spend "
                           f"₹{projected_total:,.0f} this month — "
                           f"significantly more than last month's ₹{float(last_month_total):,.0f}."
            })

    return insights