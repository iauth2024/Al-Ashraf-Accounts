from datetime import date, timedelta, timezone
import datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from num2words import num2words # type: ignore

def positive_integer_validator(value):
    if value <= 0:
        raise ValidationError('Only positive integers are allowed.')

class Receipt(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
    ]
    TYPE_CHOICES = [
        ('Donation', 'Donation'),
        ('Sadqa', 'Sadqa'),
        ('Zakat', 'Zakat'),
        ('Atiya', 'Atiya'),
        ('Fidiya', 'Fidiya'),
        ('Tasdeeq-Nama', 'Tasdeeq-Nama'),
        ('Isala-e-Sawab', 'Isala-e-Sawab'),
        ('Payment Return', 'Payment Return'),  # Added Payment Return
        ('Salary Return', 'Salary Return'),    # Added Salary Return
    ]

    manual_book_no = models.PositiveIntegerField(blank=True, null=True)
    manual_receipt_no = models.CharField(max_length=15, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    type_of_receipt = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Donation')
    mode_of_payment = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Cash')
    transaction_id = models.CharField(max_length=15, blank=True, null=True)
    cheque_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    receipt_date = models.DateField(default=date.today)

    class Meta:
        unique_together = ('manual_book_no', 'manual_receipt_no')

class HeadOfAccount(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


from num2words import num2words  # type: ignore
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime

class HeadOfAccount(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class HeadOfAccount(models.Model):
    # Placeholder for HeadOfAccount model. Replace with actual fields.
    name = models.CharField(max_length=100)

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime

class HeadOfAccount(models.Model):
    # Assuming this model exists; adjust fields as necessary.
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Voucher(models.Model):
    VOUCHER_STATUS_CHOICES = [
        ('waiting', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ]

    voucher_no = models.CharField(max_length=50, unique=True)
    paid_to = models.CharField(max_length=100)
    on_account_of = models.TextField()
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.CASCADE)
    mode_of_payment = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_in_words = models.CharField(max_length=255, blank=True)
    voucher_date = models.DateField(default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_vouchers', on_delete=models.CASCADE)
    received_by = models.CharField(max_length=100, blank=True, null=True)
    approved_by = models.ForeignKey(User, related_name='approved_vouchers', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=VOUCHER_STATUS_CHOICES, default='waiting')
    rejection_reason = models.TextField(blank=True, null=True)
    edited = models.BooleanField(default=False)
    financial_year = models.CharField(max_length=9, default='2024-25')  # Update default as needed
    sequence_number = models.PositiveIntegerField(default=1)  # Set default to 1

    class Meta:
        unique_together = ('financial_year', 'sequence_number', 'mode_of_payment')

    def __str__(self):
        return self.voucher_no

    def clean(self):
        if self.mode_of_payment in ['bank_transfer', 'cheque'] and not self.transaction_id:
            raise ValidationError('Transaction ID is required for Bank Transfer and Cheque payments.')

    def save(self, *args, **kwargs):
        # Convert amount to words if greater than zero
        if self.amount > 0:
            self.amount_in_words = num2words(self.amount)

        # Determine fiscal year (April 1st to March 31st)
        if self.voucher_date.month >= 4:
            fiscal_year_start = datetime.date(self.voucher_date.year, 4, 1)
        else:
            fiscal_year_start = datetime.date(self.voucher_date.year - 1, 4, 1)

        fiscal_year_end = datetime.date(fiscal_year_start.year + 1, 3, 31)
        year_suffix = f"{str(fiscal_year_start.year)[-2:]}-{str(fiscal_year_end.year)[-2:]}"
        
        # Update financial year field
        self.financial_year = year_suffix

        # Generate the voucher number if this is a new record
        if not self.pk:  # Only assign a new voucher number if this is a new record
            if self.mode_of_payment == 'cash':
                prefix = 'C'
            else:
                prefix = 'B'  # Use the same prefix for bank_transfer and cheque

            # Filter vouchers for the same fiscal year
            if self.mode_of_payment == 'cash':
                last_voucher = Voucher.objects.filter(
                    financial_year=self.financial_year,
                    mode_of_payment='cash'
                ).order_by('-sequence_number').first()
            else:
                last_voucher = Voucher.objects.filter(
                    financial_year=self.financial_year,
                    mode_of_payment__in=['bank_transfer', 'cheque']
                ).order_by('-sequence_number').first()

            # Determine the next sequence number based on the last voucher
            if last_voucher:
                next_number = last_voucher.sequence_number + 1
            else:
                next_number = 1  # Start from 1 if no previous voucher exists

            # Assign values for voucher number and sequence number
            self.voucher_no = f"{prefix}/{year_suffix}/{next_number}"
            self.sequence_number = next_number

        super().save(*args, **kwargs)


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Balance(models.Model):

    date = models.DateField (default=timezone.now)
    cash_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bank_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    non_cash_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_receipts_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cash receipts
    total_receipts_bank = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Bank receipts

    def __str__(self):
        return f"Cash: {self.cash_balance}, Non-Cash: {self.non_cash_balance}, Cash Receipts: {self.total_receipts_cash}, Bank Receipts: {self.total_receipts_bank}"


class Contra(models.Model):
    CONTRA_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
    ]

    contra_no = models.IntegerField(primary_key=True, unique=True)  # Manual input, must be unique
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()  # Manual input
    contra_type = models.CharField(max_length=10, choices=CONTRA_TYPE_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Contra {self.contra_no} - {self.get_contra_type_display()}"

    def delete(self, *args, **kwargs):
        self.reverse_contra_transaction()  # Reverse transaction before deletion
        super().delete(*args, **kwargs)

    def reverse_contra_transaction(self):
        # Get or create the Balance instance
        balance, created = Balance.objects.get_or_create(defaults={'cash_balance': 0, 'non_cash_balance': 0})

        # Reverse the transaction based on contra type
        if self.contra_type == 'withdraw':
            balance.non_cash_balance += self.amount  # Add back to bank closing balance
            balance.total_receipts_cash -= self.amount  # Deduct from cash receipts

        elif self.contra_type == 'deposit':
            balance.cash_balance += self.amount  # Add back to cash closing balance
            balance.total_receipts_bank -= self.amount  # Deduct from bank receipts

        balance.save()


class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    screen_time = models.FloatField(default=0)  # Time spent on the screen (in hours)
    work_time = models.FloatField(default=0)  # Actual work time (in hours)

    def __str__(self):
        return f"Activity log for {self.user.username} on {self.timestamp}"
