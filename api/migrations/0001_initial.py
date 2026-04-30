from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.CharField(max_length=255, unique=True)),
                ("username", models.CharField(max_length=255, unique=True)),
                ("telegram_id", models.CharField(max_length=255, unique=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="VerificationCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=6, unique=True)),
                ("username", models.CharField(max_length=255)),
                ("telegram_id", models.CharField(max_length=255)),
                ("expires_at", models.DateTimeField()),
            ],
            options={"ordering": ["id"]},
        ),
    ]
