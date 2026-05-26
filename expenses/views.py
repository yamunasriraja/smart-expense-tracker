# expenses/views.py

from django.shortcuts         import render, redirect, get_object_or_404
from django.contrib.auth      import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib           import messages
from .forms                   import CustomRegisterForm


# expenses/views.py
# Add these imports at the top (update your existing imports block)

from django.shortcuts              import render, redirect, get_object_or_404
from django.contrib.auth           import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib                import messages
from .forms                        import CustomRegisterForm, ExpenseForm
from .models                       import Expense
from django.http                    import HttpResponse
from django.db.models               import Sum, Q
from datetime                       import date
from dateutil.relativedelta         import relativedelta
import csv
import json





from .forms    import CustomRegisterForm, ExpenseForm, BudgetForm
from .models   import Expense, Budget
from .analytics import (
    get_monthly_summary, get_spending_change,
    get_category_breakdown, get_top_category,
    get_monthly_trend, get_recent_transactions,
    get_smart_insights,
)

# =============================================================
#  EXPENSE CRUD VIEWS
# =============================================================

@login_required
def add_expense_view(request):
    """
    GET  → Show blank expense form
    POST → Validate, save expense, redirect to expense list

    @login_required ensures only authenticated users can add expenses.
    """

    if request.method == 'POST':
        form = ExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            # commit=False gives us the object WITHOUT saving to DB yet.
            # This lets us attach the current user before the final save.
            expense.user = request.user
            expense.save()

            messages.success(
                request,
                f'Expense of ₹{expense.amount} added under '
                f'"{expense.get_category_display()}" successfully!'
            )
            return redirect('expense_list')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        # GET: pre-fill today's date so the user doesn't have to type it
        from datetime import date
        form = ExpenseForm(initial={'date': date.today()})

    return render(request, 'expenses/add_expense.html', {'form': form})


@login_required
def expense_list_view(request):
    """
    Shows all expenses belonging to the currently logged-in user.

    KEY SECURITY RULE:
    We ALWAYS filter by request.user — users must never see each other's data.
    .filter(user=request.user) is the most important line in this view.
    """

    # Base queryset — only this user's expenses, newest first
    expenses = Expense.objects.filter(user=request.user)

    # --- Optional Filtering ---
    selected_category = request.GET.get('category', '')
    selected_month    = request.GET.get('month', '')

    if selected_category:
        expenses = expenses.filter(category=selected_category)

    if selected_month:
        # selected_month comes in as 'YYYY-MM' (from an HTML month input)
        try:
            year, month = selected_month.split('-')
            expenses = expenses.filter(
                date__year=int(year),
                date__month=int(month)
            )
        except (ValueError, AttributeError):
            pass    # Ignore malformed month values

    # --- Summary Stats for this filtered view ---
    from django.db.models import Sum
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'expenses':          expenses,
        'total_amount':      total_amount,
        'expense_count':     expenses.count(),
        'category_choices':  Expense.CATEGORY_CHOICES,
        'selected_category': selected_category,
        'selected_month':    selected_month,
    }

    return render(request, 'expenses/expense_list.html', context)


@login_required
def edit_expense_view(request, pk):
    """
    GET  → Show the expense form pre-filled with existing data
    POST → Validate and update the expense

    'pk' is the primary key (ID) of the expense to edit.
    get_object_or_404 fetches the expense OR returns a 404 page if not found.

    CRITICAL: We filter by BOTH pk AND user — this prevents a logged-in user
    from editing another user's expense by guessing the URL (e.g. /expenses/42/edit/).
    This type of attack is called Insecure Direct Object Reference (IDOR).
    """

    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        # instance=expense tells the form to UPDATE this object, not create a new one

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Expense updated successfully!'
            )
            return redirect('expense_list')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = ExpenseForm(instance=expense)
        # Pre-fills the form with the existing expense data

    return render(request, 'expenses/edit_expense.html', {
        'form':    form,
        'expense': expense,
    })


@login_required
def delete_expense_view(request, pk):
    """
    POST → Delete the expense and redirect to the list.

    We only accept POST (not GET) to prevent accidental deletion
    via a link click or browser prefetch.

    Again: filter by user to prevent IDOR attacks.
    """

    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        amount   = expense.amount
        category = expense.get_category_display()

        expense.delete()

        messages.success(
            request,
            f'Expense of ₹{amount} ({category}) deleted successfully.'
        )
        return redirect('expense_list')

    # If someone tries GET on this URL, redirect them back safely
    return redirect('expense_list')




# =============================================================
#  AUTHENTICATION VIEWS
# =============================================================

def register_view(request):
    """
    Handles new user registration.

    GET  request → show the empty registration form
    POST request → validate submitted data, create user, redirect to login
    """

    # If the user is already logged in, no need to register again
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # POST: user submitted the form — process it
        form = CustomRegisterForm(request.POST)

        if form.is_valid():
            # All fields passed validation — save the new user
            user = form.save()

            # Show a success message (displayed via base.html's messages block)
            messages.success(
                request,
                f'Welcome aboard, {user.username}! Your account is ready. Please log in.'
            )

            # Redirect to login page
            return redirect('login')

        else:
            # Form has errors — show them to the user
            messages.error(
                request,
                'Please fix the errors below and try again.'
            )

    else:
        # GET: user just arrived at the page — show a blank form
        form = CustomRegisterForm()

    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
    """
    Handles user login.

    GET  request → show the empty login form
    POST request → verify credentials, log the user in, redirect to dashboard
    """

    # Already logged in? Send them to the dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # authenticate() checks credentials against the database
        # Returns a User object if valid, or None if invalid
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Credentials correct — create a session and log the user in
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect to wherever the user was trying to go,
            # or fall back to the dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)

        else:
            # Wrong username or password
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'expenses/login.html')


def logout_view(request):
    """
    Logs the user out and redirects to the login page.

    We use POST for logout (not GET) to prevent accidental/malicious logouts
    via a crafted link. Our template will submit a form via POST.
    """
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out successfully.')

    return redirect('login')


# expenses/views.py
# Replace the existing dashboard_view with this full version

from datetime import date
from .analytics import (
    get_monthly_summary,
    get_spending_change,
    get_category_breakdown,
    get_top_category,
    get_monthly_trend,
    get_recent_transactions,
    get_smart_insights,
)

@login_required
def dashboard_view(request):
    """
    Main analytics dashboard.
    Pulls all stats, chart data, and insights for the current user.
    """

    today      = date.today()
    this_year  = today.year
    this_month = today.month

    # Last month (handles January → December wrap correctly)
    from dateutil.relativedelta import relativedelta
    last_month_date = today - relativedelta(months=1)
    last_year       = last_month_date.year
    last_month      = last_month_date.month

    # --- Core monthly summaries ---
    this_month_data  = get_monthly_summary(request.user, this_year, this_month)
    last_month_data  = get_monthly_summary(request.user, last_year, last_month)

    this_month_total = this_month_data['total']
    last_month_total = last_month_data['total']
    this_month_count = this_month_data['count']

    # --- % change vs last month ---
    spending_change = get_spending_change(this_month_total, last_month_total)

    # --- Category breakdown for pie chart ---
    category_breakdown = get_category_breakdown(request.user, this_year, this_month)
    top_category       = get_top_category(category_breakdown)

    # --- 6-month trend for line chart ---
    monthly_trend = get_monthly_trend(request.user, months=6)

    # --- Recent transactions ---
    recent_expenses = get_recent_transactions(request.user, limit=6)

    # --- Smart insights ---
    insights = get_smart_insights(
        user               = request.user,
        year               = this_year,
        month              = this_month,
        category_breakdown = category_breakdown,
        this_month_total   = this_month_total,
        last_month_total   = last_month_total,
    )

    # --- Prepare chart data as JSON for Chart.js ---
    # Pie chart: category labels and totals
    pie_labels = []
    pie_totals = []
    pie_colors = [
        '#6c63ff', '#22c55e', '#f59e0b', '#ef4444',
        '#3b82f6', '#ec4899', '#14b8a6', '#f97316',
        '#8b5cf6', '#64748b',
    ]

    category_label_map = dict(__import__('expenses.models', fromlist=['Expense']).Expense.CATEGORY_CHOICES)

    for item in category_breakdown:
        pie_labels.append(category_label_map.get(item['category'], item['category'].title()))
        pie_totals.append(float(item['total']))

    # Line chart: month labels and totals
    trend_labels = [m['label'] for m in monthly_trend]
    trend_totals = [m['total'] for m in monthly_trend]

    import json
    # expenses/views.py — inside dashboard_view, BEFORE the context dict

    # --- Budget for this month ---
    budget = Budget.objects.filter(
        user=request.user,
        year=this_year,
        month=this_month
    ).first()

    budget_amount     = float(budget.amount) if budget else None
    budget_spent      = float(this_month_total)
    budget_remaining  = (budget_amount - budget_spent) if budget_amount else None
    budget_percentage = min(round((budget_spent / budget_amount) * 100, 1), 100) \
                        if budget_amount and budget_amount > 0 else None

    # Add a budget overspend insight
    if budget_amount and budget_spent > budget_amount:
        overspent_by = budget_spent - budget_amount
        insights.insert(0, {
            'type':    'danger',
            'icon':    'bi-exclamation-octagon',
            'message': f'🚨 You have exceeded your monthly budget of '
                       f'₹{budget_amount:,.2f} by ₹{overspent_by:,.2f}! '
                       f'Consider cutting back on {top_category["label"] if top_category else "expenses"}.'
        })
    elif budget_amount and budget_percentage >= 80:
        insights.insert(0, {
            'type':    'warning',
            'icon':    'bi-exclamation-triangle',
            'message': f'⚠️ You\'ve used {budget_percentage}% of your '
                       f'₹{budget_amount:,.2f} monthly budget. '
                       f'₹{budget_remaining:,.2f} remaining.'
        })
    context = {
        # Summary numbers
        'this_month_total':  this_month_total,
        'last_month_total':  last_month_total,
        'this_month_count':  this_month_count,
        'spending_change':   spending_change,
        'top_category':      top_category,

        # Recent activity
        'recent_expenses': recent_expenses,

        # Insights
        'insights': insights,

        # Chart data (passed as JSON strings to the template)
        'pie_labels': json.dumps(pie_labels),
        'pie_totals': json.dumps(pie_totals),
        'pie_colors': json.dumps(pie_colors[:len(pie_labels)]),

        'trend_labels': json.dumps(trend_labels),
        'trend_totals': json.dumps(trend_totals),

        # Month display
        'current_month_name': today.strftime('%B %Y'),
        
         'budget':            budget,
        'budget_amount':     budget_amount,
        'budget_spent':      budget_spent,
        'budget_remaining':  budget_remaining,
        'budget_percentage': budget_percentage,
    }

    return render(request, 'expenses/dashboard.html', context)








# expenses/views.py  — ADD THESE AT THE BOTTOM


# =============================================================
#  BUDGET VIEWS
# =============================================================

@login_required
def set_budget_view(request):
    """
    GET  → Show the budget form (pre-filled if a budget already exists)
    POST → Create or UPDATE the budget for the current month

    We use update_or_create() to handle both cases in one call:
    - If a budget exists for this user/year/month → update it
    - If not → create a new one
    """
    today      = date.today()
    this_year  = today.year
    this_month = today.month

    # Try to find an existing budget for this month
    existing_budget = Budget.objects.filter(
        user=request.user,
        year=this_year,
        month=this_month
    ).first()

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=existing_budget)

        if form.is_valid():
            budget       = form.save(commit=False)
            budget.user  = request.user
            budget.year  = this_year
            budget.month = this_month
            budget.save()

            messages.success(
                request,
                f'Budget of ₹{budget.amount:,.2f} set for '
                f'{today.strftime("%B %Y")} successfully!'
            )
            return redirect('dashboard')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = BudgetForm(instance=existing_budget)

    # Calculate current spending so the form shows live context
    monthly_data = get_monthly_summary(request.user, this_year, this_month)

    return render(request, 'expenses/set_budget.html', {
        'form':            form,
        'existing_budget': existing_budget,
        'monthly_total':   monthly_data['total'],
        'current_month':   today.strftime('%B %Y'),
    })


# =============================================================
#  CSV EXPORT VIEW
# =============================================================

@login_required
def export_csv_view(request):
    """
    Generates and downloads a CSV file of the user's expenses.

    HttpResponse with content_type='text/csv' tells the browser
    to treat the response as a file download, not a webpage.

    Supports optional filtering by month via GET parameter.
    """
    today = date.today()

    # Optional month filter (format: YYYY-MM)
    month_filter = request.GET.get('month', '')

    # Start with all of this user's expenses
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    # Apply month filter if provided
    if month_filter:
        try:
            year, month = month_filter.split('-')
            expenses = expenses.filter(
                date__year=int(year),
                date__month=int(month)
            )
            filename = f'expenses_{month_filter}.csv'
        except ValueError:
            filename = f'expenses_all_{today.strftime("%Y%m%d")}.csv'
    else:
        filename = f'expenses_all_{today.strftime("%Y%m%d")}.csv'

    # Create the HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # CSV Header Row
    writer.writerow([
        'Date',
        'Category',
        'Amount (INR)',
        'Description',
        'Added On',
    ])

    # Data Rows
    total = 0
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%d-%m-%Y'),
            expense.get_category_display(),
            f'{expense.amount:.2f}',
            expense.description or '',
            expense.created_at.strftime('%d-%m-%Y %H:%M'),
        ])
        total += expense.amount

    # Summary Footer Row
    writer.writerow([])
    writer.writerow(['', 'TOTAL', f'{total:.2f}', '', ''])

    return response


# =============================================================
#  SEARCH VIEW
# =============================================================

@login_required
def search_view(request):
    """
    Searches expenses by description, category label, or amount.

    Uses Django's Q objects for OR queries:
    Q(description__icontains=q) | Q(category__icontains=q)
    means "description contains q OR category contains q"

    icontains = case-insensitive LIKE '%q%' in SQL
    """
    query    = request.GET.get('q', '').strip()
    expenses = []
    total    = 0
    count    = 0

    if query:
        expenses = Expense.objects.filter(
            user=request.user
        ).filter(
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).order_by('-date')

        count = expenses.count()
        total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'expenses/search.html', {
        'query':    query,
        'expenses': expenses,
        'count':    count,
        'total':    total,
    })