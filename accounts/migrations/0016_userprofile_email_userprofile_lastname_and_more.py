# Generated by Django 4.2.7 on 2023-11-28 15:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_alter_company_cantidad_empleados"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="lastname",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="name",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]