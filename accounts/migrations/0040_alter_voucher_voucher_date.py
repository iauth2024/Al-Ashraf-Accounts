# Generated by Django 5.0.6 on 2024-07-23 11:22

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0039_rename_payment_purpose_voucher_on_account_of_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucher',
            name='voucher_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
