# Generated by Django 5.2.2 on 2025-07-02 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_alter_product_discription_variation'),
    ]

    operations = [
        migrations.CreateModel(
            name='VariationManager',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
    ]
