from django.db import models
from django.contrib.auth.models import User
from typing import Literal

class Category(models.Model):
    name: str = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES: list[tuple[str, str]] = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    title: str = models.CharField(max_length=200)
    description: str = models.TextField(blank=True, default="")
    priority: str = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    is_completed: bool = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    user: User = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    category: Category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")

    def __str__(self) -> str:
        return f"{self.title} ({self.priority})"