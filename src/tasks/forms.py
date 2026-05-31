from django import forms
from .models import Task, Category
from typing import Any

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields: list[str] = ['title', 'description', 'priority', 'category', 'due_date']
        widgets: dict[str, Any] = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your task...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }