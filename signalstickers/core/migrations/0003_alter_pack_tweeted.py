# Generated by Django 3.2.15 on 2022-08-24 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20220206_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pack',
            name='tweeted',
            field=models.BooleanField(default=True),
        ),
    ]