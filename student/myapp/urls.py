from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page,name='login'),
    path('register/',views.register_page,name='register'),
    path('home/',views.home,name='home'),
    path('teacher/',views.teacher_home,name='teacher_home'),
    path('admin_home/',views.admin_home,name='admin_home'),
]
