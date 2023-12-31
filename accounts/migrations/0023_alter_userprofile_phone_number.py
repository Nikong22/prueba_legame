# Generated by Django 4.2.7 on 2023-12-05 18:39

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0022_userprofile_document_number_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True,
                help_text="Número de teléfono con prefijo internacional",
                max_length=128,
                region=None,
            ),
        ),
    ]
