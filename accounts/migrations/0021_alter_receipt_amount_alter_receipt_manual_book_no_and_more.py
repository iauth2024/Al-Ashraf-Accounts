# Generated by Django 5.0.6 on 2024-07-16 11:34

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_receipt_amount_alter_receipt_manual_book_no_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='amount',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='manual_book_no',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[accounts.models.positive_integer_validator]),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='phone',
            field=models.PositiveIntegerField(validators=[accounts.models.positive_integer_validator]),
        ),
    ]
