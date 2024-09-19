# Generated by Django 5.0.6 on 2024-06-22 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_receipt_receipt_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='amount',
            field=models.DecimalField(decimal_places=2, default='000', max_digits=10),
            preserve_default=False,
        ),
    ]
