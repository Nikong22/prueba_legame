# Generated by Django 4.2.7 on 2023-11-21 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_jobpost_description_jobpost_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='phone_number',
            field=models.CharField(default='', max_length=15),
            preserve_default=False,
        ),
    ]