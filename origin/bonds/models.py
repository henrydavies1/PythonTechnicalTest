from django.db import models


class Bond(models.Model):

    isin = models.CharField(max_length=30)
    size = models.IntegerField()
    currency = models.CharField(max_length=3)
    maturity = models.DateField()
    lei = models.CharField(max_length=30)
    legal_name = models.CharField(max_length=100)
