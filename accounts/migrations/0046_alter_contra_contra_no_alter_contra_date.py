# Generated by Django 5.1 on 2024-09-21 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0045_alter_contra_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contra',
            name='contra_no',
            field=models.IntegerField(primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='contra',
            name='date',
            field=models.DateField(),
        ),
    ]
