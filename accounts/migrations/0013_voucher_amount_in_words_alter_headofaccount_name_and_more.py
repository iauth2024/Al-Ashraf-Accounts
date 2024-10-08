# Generated by Django 5.0.6 on 2024-06-25 07:06

import accounts.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_headofaccount_voucher_amount_voucher_approved_by_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='amount_in_words',
            field=models.TextField(default='zero'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='headofaccount',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='amount',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='manual_book_no',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='manual_receipt_no',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='phone',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_vouchers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='head_of_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.headofaccount'),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='paid_to',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='payment_purpose',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='purchased_by',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
