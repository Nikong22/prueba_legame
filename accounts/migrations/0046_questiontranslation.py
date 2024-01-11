# Generated by Django 4.2.7 on 2024-01-10 22:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0045_rename_content_es_faq_content_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[("es", "Español"), ("it", "Italiano")], max_length=2
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("short_answer", models.TextField()),
                ("complete_answer", models.TextField()),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="accounts.question",
                    ),
                ),
            ],
            options={
                "unique_together": {("question", "language")},
            },
        ),
    ]
