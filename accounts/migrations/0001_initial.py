# Generated by Django 5.0.6 on 2024-06-16 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('manual_book_no', models.CharField(max_length=50)),
                ('manual_receipt_no', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=15)),
                ('address', models.TextField()),
                ('type_of_receipt', models.CharField(max_length=50)),
                ('mode_of_payment', models.CharField(choices=[('Cash', 'Cash'), ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer'), ('Cheque', 'Cheque')], default='Cash', max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('cheque_number', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
    ]
