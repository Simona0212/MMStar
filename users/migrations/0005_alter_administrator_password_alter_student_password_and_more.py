# Generated by Django 5.1.4 on 2024-12-16 04:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_alter_administrator_email_alter_student_email_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="administrator",
            name="Password",
            field=models.CharField(default="123456", max_length=255),
        ),
        migrations.AlterField(
            model_name="student",
            name="Password",
            field=models.CharField(default="123456", max_length=255),
        ),
        migrations.AlterField(
            model_name="teacher",
            name="Password",
            field=models.CharField(default="123456", max_length=255),
        ),
    ]
