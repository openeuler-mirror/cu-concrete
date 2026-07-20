from django.urls import path
from . import views

urlpatterns = [
    path('execute-playbook/', views.execute_playbook, name='execute-playbook'),
    path('get-results/', views.get_results, name='get-results'),
    path('pool-list/', views.pool_list, name='pool-list'),
    path('tasks/', views.list_tasks, name='list-tasks'),
    path('task-detail/', views.get_task, name='get-task'),
    path('task-logs/', views.get_task_logs_view, name='get-task-logs'),
