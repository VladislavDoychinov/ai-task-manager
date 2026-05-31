from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.db.models import Count
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Category
from .forms import TaskForm, UserRegisterForm
from typing import Any, Dict

def get_analytics_data(user_id: int) -> Dict[str, Any]:
    total: int = Task.objects.filter(user_id=user_id).count()
    completed: int = Task.objects.filter(user_id=user_id, is_completed=True).count()
    pending: int = total - completed
    
    priority_stats = Task.objects.filter(user_id=user_id).values('priority').annotate(count=Count('id'))
    
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': round((completed / total * 100), 1) if total > 0 else 0,
        'priority_stats': priority_stats
    }

def task_list(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    tasks = Task.objects.filter(user=user).order_by('-created_at')
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = user
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()

    analytics = get_analytics_data(user.id)
    
    context: Dict[str, Any] = {
        'tasks': tasks,
        'categories': categories,
        'form': form,
        'analytics': analytics
    }
    return render(request, 'tasks/dashboard.html', context)

def toggle_task(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('task_list')

def delete_task(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('task_list')

def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('task_list')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_list')
    else:
        form = UserRegisterForm()
    return render(request, 'tasks/register.html', {'form': form})

def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('task_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('task_list')
    else:
        form = AuthenticationForm()
    return render(request, 'tasks/login.html', {'form': form})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')