# Generated by Django 3.1.5 on 2021-01-14 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stickers', '0003_pack_tweeted'),
    ]

    operations = [
        migrations.AddField(
            model_name='pack',
            name='id_cover',
            field=models.IntegerField(default=0),
        ),
    ]
