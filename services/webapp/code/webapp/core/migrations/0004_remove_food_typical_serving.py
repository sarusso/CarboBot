# Generated by Django 5.0.3 on 2025-03-11 10:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_food_large_piece_food_medium_piece_food_small_piece'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='food',
            name='typical_serving',
        ),
    ]
