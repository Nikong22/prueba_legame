# Generated by Django 4.2.7 on 2023-12-18 21:42

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0039_jobpost_comuna_it_jobpost_provincia_it_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='Número de teléfono con prefijo internacional', max_length=128, region=None),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='country',
            field=models.CharField(choices=[('AR', 'Argentina'), ('IT', 'Italia')], default='AR', max_length=2),
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='province_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
