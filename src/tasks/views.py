from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.db.models import Count
from .models import Task, Category
from .forms import TaskForm
from typing import Any, Dict

def get_analytics_data(user_id: int) -> Dict[str, Any]:
    """
    Pure Python function to calculate user task statistics.
    Excellent candidate to showcase during your code review defense!
    """
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
        return HttpResponse("Please log in first (Your teammate's module).", status=401)

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
    """Toggles a task status between completed and pending"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('task_list')

def delete_task(request: HttpRequest, task_id: int) -> HttpResponse:
    """Deletes a specific task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('task_list')