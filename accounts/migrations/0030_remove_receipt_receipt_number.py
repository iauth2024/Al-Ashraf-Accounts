# Generated by Django 5.0.6 on 2024-07-20 05:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0029_alter_receipt_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='receipt',
            name='receipt_number',
        ),
    ]
