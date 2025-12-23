from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page,name='login'),
    path('register/',views.register_page,name='register'),
    path('activate/<str:token>/', views.activate_account, name='activate'),
    path('home/',views.home,name='home'),
    path('profile/',views.user_profile,name = 'user_profile'),
    path('delete',views.course_del,name = 'delete_course'),
    path('logout',views.user_logout,name = 'user_logout'),
    path('edit_profile/',views.edit_user,name = 'edit_user'),
    path('user_course/',views.user_course,name = 'user_course'),
    path('enroll_course/<int:id>',views.enroll_course,name = 'enroll_course'),
    path('teacher/',views.teacher_home,name='teacher_home'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path('add_roles/',views.add_roles,name='add_roles'),

]
