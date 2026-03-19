from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid

# --- 1. NGƯỜI DÙNG (Custom User) ---
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    ROLE_CHOICES = [
        ('ADMIN', 'ADMIN'),
        ('SALE', 'SALE'),
        ('KHO', 'KHO'),
        ('KE_TOAN', 'KE_TOAN'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # Sửa lỗi Reverse Accessor Clashes bằng related_name
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True
    )

    class Meta:
        db_table = 'users'