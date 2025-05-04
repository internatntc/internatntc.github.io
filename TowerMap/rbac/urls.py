from django.urls import path
from . import views

app_name = 'rbac'
urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-role/', views.create_role, name='create_role'),
    path('assign-services/<int:role_id>/',
         views.assign_services, name='assign_services'),
    path('assign-user-role/<int:user_id>/',
         views.assign_user_role, name='assign_user_role'),
    path('user-roles-view/',
         views.user_roles_view, name='user_roles_view'),
    path('create-user/', views.create_user_view, name='create_user'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),

]
