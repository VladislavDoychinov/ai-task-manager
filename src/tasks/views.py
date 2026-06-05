import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.db.models import Count
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Category
from .forms import TaskForm, UserRegisterForm
from typing import Any, Dict
from django.utils import timezone

try:
    from google import genai
except ImportError:
    genai = None

try:
    from dotenv import load_dotenv
    load_dotenv() 
except ImportError:
    pass

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

    ai_recommendation = "You have no pending tasks to analyze at the moment."
    
    if genai is None:
        ai_recommendation = "[Error: 'google-genai' package is not installed.]"
    elif tasks.exists():
        tasks_text = "\n".join([
            f"- {t.title} ({t.priority} priority, Category: {t.category.name if t.category else 'None'}) - {'Completed' if t.is_completed else 'Pending'}" 
            for t in tasks
        ])
        
        prompt = f"""
        You are a highly efficient personal productivity assistant. Here is a list of the user's tasks:
        {tasks_text}
        
        Provide a brief, motivating piece of advice (maximum 2 sentences) in English on which task they should tackle first and how to organize their day better.
        """
        
        try:
            api_key_env = os.getenv("GEMINI_API_KEY")
            
            if not api_key_env:
                ai_recommendation = "[Configuration Error: GEMINI_API_KEY is missing from your local .env file! Please check the instructions.]"
            else:
                client = genai.Client(api_key=api_key_env)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                ai_recommendation = response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                ai_recommendation = "AI Assistant is resting due to high demand (Rate limit reached). Please refresh the page in a few seconds."
            else:
                ai_recommendation = f"Error connecting to Gemini API: {str(e)}"

    context: Dict[str, Any] = {
        'tasks': tasks,
        'categories': categories,
        'form': form,
        'analytics': analytics,
        'ai_recommendation': ai_recommendation,
        'datetime_now': timezone.now(),  
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