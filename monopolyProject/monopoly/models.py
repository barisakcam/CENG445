from typing import Any
from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, email, password, full_name):
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            full_name=full_name
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
class User(AbstractUser):
    username = models.CharField(max_length=16, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=32)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "full_name"]
