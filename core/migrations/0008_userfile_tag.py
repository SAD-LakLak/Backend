# Generated by Django 5.1.4 on 2025-03-09 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_userfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfile',
            name='tag',
            field=models.CharField(default='tag', max_length=255),
            preserve_default=False,
        ),
    ]
