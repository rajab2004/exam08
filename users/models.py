from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Xaridor"
        SELLER = "seller", "Sotuvchi"

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)


    username = models.CharField(max_length=150, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.id} | {self.role} | {self.telegram_id}"