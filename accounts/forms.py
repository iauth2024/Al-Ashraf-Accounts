

import datetime
from django import forms
from .models import Receipt



class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = [
            'manual_book_no', 'manual_receipt_no', 'name', 'phone', 'address', 
            'type_of_receipt', 'mode_of_payment', 'transaction_id', 'cheque_number', 
            'amount', 'receipt_date'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set manual_receipt_no to editable for all payment modes
        self.fields['manual_receipt_no'].widget.attrs['readonly'] = False

    def clean(self):
        cleaned_data = super().clean()
        mode_of_payment = cleaned_data.get('mode_of_payment')
        
        # Validation for manual_book_no and manual_receipt_no for all types of payments
        manual_book_no = cleaned_data.get('manual_book_no')
        manual_receipt_no = cleaned_data.get('manual_receipt_no')
        
        if not manual_book_no:
            self.add_error('manual_book_no', 'Manual Book Number is required for all payment types.')
        
        if not manual_receipt_no:
            self.add_error('manual_receipt_no', 'Manual Receipt Number is required for all payment types.')
        
        # Check if the combination of manual_book_no and manual_receipt_no already exists
        if manual_book_no and manual_receipt_no:
            if Receipt.objects.filter(manual_book_no=manual_book_no, manual_receipt_no=manual_receipt_no).exists():
                self.add_error('manual_receipt_no', 'This combination of Manual Book Number and Manual Receipt Number already exists.')
        
        # Uniqueness validation for transaction_id
        transaction_id = cleaned_data.get('transaction_id')
        if transaction_id:
            if Receipt.objects.filter(transaction_id=transaction_id).exists():
                self.add_error('transaction_id', 'Transaction ID must be unique.')
        
        # Uniqueness validation for cheque_number
        cheque_number = cleaned_data.get('cheque_number')
        if cheque_number:
            if Receipt.objects.filter(cheque_number=cheque_number).exists():
                self.add_error('cheque_number', 'Cheque Number must be unique.')
        
        return cleaned_data





from .models import Receipt, Voucher
from django import forms
from .models import Voucher

class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = [
            'voucher_no', 'paid_to', 'on_account_of', 'head_of_account',
            'mode_of_payment', 'transaction_id', 'amount', 'voucher_date',
            'received_by'
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        voucher_type = cleaned_data.get('voucher_type')
        financial_year = cleaned_data.get('financial_year')
        sequence_number = cleaned_data.get('sequence_number')

        # Ensure the combination is unique
        if Voucher.objects.filter(voucher_type=voucher_type, financial_year=financial_year, sequence_number=sequence_number).exists():
            raise forms.ValidationError('The combination of Voucher Type, Financial Year, and Sequence Number must be unique.')

        return cleaned_data


class ApprovalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Fetch the user from kwargs
        super(ApprovalForm, self).__init__(*args, **kwargs)
        
        # Customize approved_by field choices based on the current user
        if user:
            self.fields['approved_by'].queryset = user.__class__.objects.filter(username=user.username)
    
    class Meta:
        model = Voucher
        fields = ['approved_by', 'status', 'rejection_reason', 'edited']

class RejectionForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = ['rejection_reason']




from django import forms
from .models import Voucher

class VoucherFilterForm(forms.Form):
    voucher_no = forms.CharField(required=False, label='Voucher No')
    paid_to = forms.CharField(required=False, label='Paid To')
    on_account_of = forms.CharField(required=False, label='On Account Of')
    head_of_account = forms.CharField(required=False, label='Head of Account')
    mode_of_payment = forms.ChoiceField(choices=[('', 'All')] + Voucher.PAYMENT_MODE_CHOICES, required=False, label='Mode of Payment')
    transaction_id = forms.CharField(required=False, label='Transaction ID')
    amount_min = forms.DecimalField(required=False, label='Amount Min', min_value=0)
    amount_max = forms.DecimalField(required=False, label='Amount Max', min_value=0)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')
    received_by = forms.CharField(required=False, label='Received By')
    status = forms.ChoiceField(choices=[('', 'All')] + Voucher.VOUCHER_STATUS_CHOICES, required=False, label='Status')

#################################################################################################################

from django import forms
from datetime import date

DATE_RANGE_CHOICES = [
    ('today', 'Today'),
    ('yesterday', 'Yesterday'),
    ('this_week', 'This Week'),
    ('last_week', 'Last Week'),
    ('this_month', 'This Month'),
    ('last_month', 'Last Month'),
    ('custom', 'Custom Range')
]

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES, required=False, initial='today')

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')

        if date_range == 'custom':
            if not cleaned_data.get('start_date') or not cleaned_data.get('end_date'):
                raise forms.ValidationError('Start date and end date are required for custom range.')


from django import forms
from .models import Contra

from django import forms
from .models import Contra  # Ensure Contra is correctly imported if needed

class ContraForm(forms.ModelForm):
    class Meta:
        model = Contra
        fields = ['contra_no', 'amount', 'contra_type', 'date']  # Include contra_no in fields

    def clean_contra_no(self):
        contra_no = self.cleaned_data.get('contra_no')
        if Contra.objects.filter(contra_no=contra_no).exists():
            raise forms.ValidationError("This contra number already exists. Please choose a different one.")
        return contra_no

from django import forms
from .models import Contra  # Ensure Contra is correctly imported if needed

class ContraFilterForm(forms.Form):
    contra_no = forms.CharField(required=False)
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    amount_min = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    amount_max = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    contra_type = forms.ChoiceField(choices=Contra.CONTRA_TYPE_CHOICES, required=False)
    performed_by = forms.CharField(required=False)



class UploadExcelForm(forms.Form):
    excel_file = forms.FileField()
from django import forms

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()
from django import forms
from django.utils import timezone

DATE_RANGE_CHOICES = [
    ('today', 'Today'),
    ('yesterday', 'Yesterday'),
    ('this_week', 'This Week'),
    ('last_week', 'Last Week'),
    ('this_month', 'This Month'),
    ('last_month', 'Last Month'),
    ('custom', 'Custom'),
]

class DateRangeForm(forms.Form):
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES, required=False)
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
