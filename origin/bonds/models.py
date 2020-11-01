from django.db import models
from django.contrib.auth.models import User


class Bond(models.Model):

    isin = models.CharField(max_length=30)
    size = models.IntegerField()
    currency = models.CharField(max_length=3)
    maturity = models.DateField()
    lei = models.CharField(max_length=30)
    legal_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
