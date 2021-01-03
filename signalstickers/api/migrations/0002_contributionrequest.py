# Generated by Django 3.1.4 on 2021-01-03 19:03

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContributionRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('client_ip', models.GenericIPAddressField(protocol='IPv4')),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.botpreventionquestion')),
            ],
            options={
                'db_table': 'contributionrequests',
            },
        ),
    ]
