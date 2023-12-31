# Generated by Django 4.2.7 on 2023-11-22 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_company_city_company_province'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobpost',
            name='location',
        ),
        migrations.AddField(
            model_name='jobpost',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='jobpost',
            name='country',
            field=models.CharField(choices=[('AR', 'Argentina'), ('IT', 'Italia')], default='', max_length=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jobpost',
            name='province',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
