# Generated by Django 4.2.7 on 2023-12-10 20:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0032_faq"),
    ]

    operations = [
        migrations.RenameField(
            model_name="faq",
            old_name="answer",
            new_name="content",
        ),
        migrations.RenameField(
            model_name="faq",
            old_name="question",
            new_name="title",
        ),
        migrations.RemoveField(
            model_name="faq",
            name="order",
        ),
    ]
