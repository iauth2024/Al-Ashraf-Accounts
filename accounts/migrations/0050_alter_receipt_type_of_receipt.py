# Generated by Django 5.1 on 2024-09-24 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_alter_voucher_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='type_of_receipt',
            field=models.CharField(choices=[('Donation', 'Donation'), ('Sadqa', 'Sadqa'), ('Zakat', 'Zakat'), ('Atiya', 'Atiya'), ('Fidiya', 'Fidiya'), ('Tasdeeq-Nama', 'Tasdeeq-Nama'), ('Isala-e-Sawab', 'Isala-e-Sawab'), ('Payment Return', 'Payment Return'), ('Salary Return', 'Salary Return')], default='Donation', max_length=50),
        ),
    ]
