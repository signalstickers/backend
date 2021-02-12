# Generated by Django 3.1.6 on 2021-02-11 21:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stickers', '0004_pack_id_cover'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowcasedPack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('pack', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stickers.pack')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
