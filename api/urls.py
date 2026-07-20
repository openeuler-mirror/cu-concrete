from django.urls import path
from . import views

urlpatterns = [
    path('execute-playbook/', views.execute_playbook, name='execute-playbook'),
    path('get-results/', views.get_results, name='get-results'),
    path('pool-list/', views.pool_list, name='pool-list'),
    path('tasks/', views.list_tasks, name='list-tasks'),
    path('task-detail/', views.get_task, name='get-task'),
    path('task-logs/', views.get_task_logs_view, name='get-task-logs'),
    path('pool-hosts/', views.pool_hosts, name='pool-hosts'),
    path('harden-items/', views.harden_items_list, name='harden-items'),
    path('generate-config/', views.generate_config, name='generate-config'),
    path('from-pool-get-configs/', views.from_pool_get_configs, name='from-pool-get-configs'),
    path('from-file-get-config/', views.from_file_get_config, name='from-file-get-config'),
    path('save-conf-content/', views.save_conf_content, name='save-conf-content'),
    path('delete-config/', views.delete_conf, name='delete-conf'),
    path('get-conf-level/', views.get_conf_level, name='get-conf-level'),
    path('save-generated-config/', views.save_generated_config, name='save-generated-config')
]
