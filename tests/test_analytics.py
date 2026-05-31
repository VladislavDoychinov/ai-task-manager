import pytest  # type: ignore
from django.contrib.auth.models import User
from src.tasks.models import Task, Category
from src.tasks.views import get_analytics_data

@pytest.mark.django_db
def test_analytics_calculation() -> None:
    user = User.objects.create_user(username="testuser", password="password")
    category = Category.objects.create(name="Work")

    Task.objects.create(title="Task 1", is_completed=True, user=user, category=category)
    Task.objects.create(title="Task 2", is_completed=False, user=user, category=category)
    
    data = get_analytics_data(user.id)
    
    assert data['total'] == 2
    assert data['completed'] == 1
    assert data['pending'] == 1
    assert data['completion_rate'] == 50.0