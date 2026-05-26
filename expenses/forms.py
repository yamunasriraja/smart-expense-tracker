
# expenses/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomRegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm to add:
    - Email field (required)
    - Cleaner field labels and widgets
    - Custom validation
    
    Django's UserCreationForm already gives us:
    - username field
    - password1 (password)
    - password2 (confirm password)
    - Password match validation
    - Password strength validation
    We just ADD email and customize the look.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class':       'form-control',
            'placeholder': 'you@example.com',
        }),
        help_text='We will never share your email with anyone.'
    )

    class Meta:
        model  = User                                         # Use Django's built-in User model
        fields = ['username', 'email', 'password1', 'password2']  # Field order on the form

    def __init__(self, *args, **kwargs):
        """
        Called when the form is created.
        We use this to add Bootstrap CSS classes and placeholders
        to every field automatically — so we don't repeat ourselves.
        """
        super().__init__(*args, **kwargs)

        # Customize username field
        self.fields['username'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Choose a username',
        })
        self.fields['username'].help_text = (
            'Letters, digits and @/./+/-/_ only. Max 150 characters.'
        )

        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Create a strong password',
        })
        self.fields['password1'].help_text = (
            'Minimum 8 characters. Cannot be entirely numeric.'
        )

        self.fields['password2'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Repeat your password',
        })
        self.fields['password2'].help_text = ''   # Hide the redundant help text

    def clean_email(self):
        """
        Custom validation for the email field.
        'clean_<fieldname>' methods are called automatically by Django
        when the form is validated. If we raise a ValidationError,
        the form is rejected and the error is shown to the user.
        """
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists. Please log in instead.'
            )

        return email

    def save(self, commit=True):
        """
        Override save() to also store the email field.
        UserCreationForm.save() only saves username + password by default.
        """
        user = super().save(commit=False)    # Create user object but don't save yet
        user.email = self.cleaned_data['email']

        if commit:
            user.save()                      # Now save to the database

        return user
    
    
    
    
    
    
    
    # expenses/forms.py
# (Add this BELOW your existing CustomRegisterForm class)

from .models import Expense   # Add this import at the top of the file


class ExpenseForm(forms.ModelForm):
    """
    A ModelForm for the Expense model.

    ModelForm automatically:
    - Creates form fields from model fields
    - Validates data against model constraints (max_digits, max_length, etc.)
    - Has a .save() method that writes directly to the database

    We just customize the widgets (HTML attributes) to match our UI.
    """

    class Meta:
        model  = Expense
        fields = ['amount', 'category', 'date', 'description']
        # We exclude 'user' because we assign it in the VIEW, not from user input.
        # Never let users assign their own user field — that's a security hole.

        widgets = {
            'amount': forms.NumberInput(attrs={
                'class':       'form-control',
                'placeholder': '0.00',
                'min':         '0.01',
                'step':        '0.01',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',       # Renders as a native date picker in browsers
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'placeholder': 'Optional: What was this expense for?',
                'rows':        3,
            }),
        }

        labels = {
            'amount':      'Amount (₹)',
            'category':    'Category',
            'date':        'Date',
            'description': 'Description',
        }

    def clean_amount(self):
        """
        Validate that the amount is a positive number greater than zero.
        Django calls clean_<fieldname>() automatically during form.is_valid().
        """
        amount = self.cleaned_data.get('amount')

        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                'Amount must be greater than ₹0.00.'
            )

        return amount
    
    
    
    
    
    # expenses/forms.py
# Add this at the bottom, after ExpenseForm

from .models import Expense, Budget     # update the import line at the top


class BudgetForm(forms.ModelForm):
    """
    Form for setting or updating a monthly budget.
    Only the amount field is user-editable;
    month, year, and user are set in the view.
    """

    class Meta:
        model  = Budget
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class':       'form-control form-control-lg',
                'placeholder': 'e.g. 15000',
                'min':         '1',
                'step':        '100',
            }),
        }
        labels = {'amount': 'Monthly Budget Limit (₹)'}

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Budget must be greater than ₹0.')
        return amount