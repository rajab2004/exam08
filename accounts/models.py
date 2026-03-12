from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    Role_Choices = [
        ('admin', 'Admin'),
        ('user', 'User')
    ]

    role = models.CharField(max_length=50, choices=Role_Choices, default="user")
    created_at=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.username