from datetime import date, timedelta, timezone
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

    ]

    manual_book_no = models.PositiveIntegerField(blank=True, null=True)
    manual_receipt_no = models.CharField(max_length=15, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # Changed to CharField
    address = models.CharField(max_length=300, blank=True, null=True)
    type_of_receipt = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Donation')
    mode_of_payment = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Cash')
    transaction_id = models.CharField(max_length=15, blank=True, null=True)
    cheque_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.PositiveIntegerField(validators=[positive_integer_validator])
    receipt_date = models.DateField(default=date.today)  # Default to current date

    class Meta:
        unique_together = ('manual_book_no', 'manual_receipt_no')

    @staticmethod
    def get_next_receipt_number(mode_of_payment):
        last_receipt = Receipt.objects.filter(
            mode_of_payment=mode_of_payment
        ).order_by('-manual_receipt_no').first()

        if last_receipt and last_receipt.manual_receipt_no:
            try:
                last_number = int(last_receipt.manual_receipt_no.split('-')[-1])
                return f'{last_number + 1:06d}'
            except ValueError:
                return '000001'
        return '000001'
class HeadOfAccount(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


from num2words import num2words # type: ignore
from django.utils import timezone
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User  # Assuming you're using Django's built-in User model

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
    on_account_of = models.TextField()  # Renamed field
    head_of_account = models.ForeignKey('HeadOfAccount', on_delete=models.CASCADE)
    mode_of_payment = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_in_words = models.CharField(max_length=255, blank=True)
    voucher_date = models.DateField(default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_vouchers', on_delete=models.CASCADE)
    received_by = models.CharField(max_length=100, blank=True, null=True)  # Renamed field
    approved_by = models.ForeignKey(User, related_name='approved_vouchers', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=VOUCHER_STATUS_CHOICES, default='waiting')
    rejection_reason = models.TextField(blank=True, null=True)
    edited = models.BooleanField(default=False)

    def __str__(self):
        return self.voucher_no


    def clean(self):
        if self.mode_of_payment in ['bank_transfer', 'cheque'] and not self.transaction_id:
            raise ValidationError('Transaction ID is required for Bank Transfer and Cheque payments.')
    
    def save(self, *args, **kwargs):
        if self.amount > 0:
            self.amount_in_words = num2words(self.amount)  # Calculate amount in words
        super().save(*args, **kwargs)

    def __str__(self):
        return self.voucher_no



from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Contra(models.Model):
    CONTRA_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
    ]

    contra_no = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    contra_type = models.CharField(max_length=10, choices=CONTRA_TYPE_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Contra {self.contra_no} - {self.get_contra_type_display()}"

    def delete(self, *args, **kwargs):
        self.reverse_contra_transaction()
        super().delete(*args, **kwargs)

    def reverse_contra_transaction(self):
        balance = Balance.objects.first()  # Assuming you have a single balance record

        if self.contra_type == 'withdraw':
            balance.non_cash_balance += self.amount
            balance.cash_balance -= self.amount
        elif self.contra_type == 'deposit':
            balance.cash_balance += self.amount
            balance.non_cash_balance -= self.amount

        balance.save()


class Balance(models.Model):
    cash_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    non_cash_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Cash: {self.cash_balance}, Non-Cash: {self.non_cash_balance}"


from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    screen_time = models.FloatField(default=0)
    work_time = models.FloatField(default=0)

    def __str__(self):
        return f"Activity log for {self.user.username} on {self.timestamp}"
