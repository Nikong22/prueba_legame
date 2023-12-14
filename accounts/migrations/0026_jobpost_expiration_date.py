# Generated by Django 4.2.7 on 2023-12-06 21:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0025_jobpost_application_limit"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="expiration_date",
            field=models.DateField(
                default=django.utils.timezone.now, verbose_name="Fecha de vencimiento"
            ),
        ),
    ]