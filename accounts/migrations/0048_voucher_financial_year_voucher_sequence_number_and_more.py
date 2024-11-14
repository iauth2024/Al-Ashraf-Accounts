# Generated by Django 5.1 on 2024-09-24 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_balance_total_receipts_bank_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='financial_year',
            field=models.CharField(default='2024-25', max_length=9),
        ),
        migrations.AddField(
            model_name='voucher',
            name='sequence_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='headofaccount',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='voucher',
            unique_together={('financial_year', 'sequence_number')},
        ),
    ]