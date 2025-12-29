import hashlib
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.core.mail import send_mail
# Create your views here.
from .forms import reg_form
from .models import reg_model,course_model
from django.db.models import Q
from .decorators import role_requeried
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.conf import settings
import uuid
from django.contrib import messages
from django.db.models import Sum

token_generator = PasswordResetTokenGenerator()


def register_page(request):
    if request.method == 'POST':
        form = reg_form(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            raw_pass = form.cleaned_data['u_password']
            user.u_password = hashlib.sha256(raw_pass.encode('utf-8')).hexdigest()
            user.u_confirm = ''
            user.is_active = False
            user.activation_token = str(uuid.uuid4())
            user.save()

            
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'token': user.activation_token})
            )

            send_mail(
                'Activate your account',
                f'Hi {user.u_username}, click the link to activate your account: {activation_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.u_email],
                fail_silently=False,
            )

            messages.success(request,"link sented")
            return redirect('login')
        else:
            return render(request, 'myapp/register.html', {'form': form})
    else:
        form = reg_form()
        return render(request, 'myapp/register.html', {'form': form})
    

def activate_account(request,token):
   user=get_object_or_404(reg_model,activation_token = token)
   if user.role == None:
       user.role = 'student'
       user.activation_token = None
       user.is_active = True
       user.save()
       messages.success(request,"activation successful")
       return redirect("login")
   else:
       messages.success(request,"account already activated")
       return redirect("login")

def resend_link(request):
    email = request.POST.get("email")
    obj = reg_model.objects.filter(u_email = email)
    if obj.exists():
        user = obj.first()
        if user.role == None:
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'token': user.activation_token})
            )

            send_mail(
                'Activate your account',
                f'Hi {user.u_username}, click the link to activate your account: {activation_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.u_email],
                fail_silently=False,
            )
            messages.success(request,"link sented")
            return redirect('login')
        else:
            messages.warning(request,"your already activated")
            return redirect('login')


    return render(request,'myapp/resend_link.html')
   



def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        hashed_password = hashlib.sha256(
            password.encode('utf-8')
        ).hexdigest()

        try:
            user = reg_model.objects.get(
                Q(u_email=email) & Q(u_password=hashed_password)
            )
        except reg_model.DoesNotExist:
            messages.error(request, "Invalid email or password")
            return render(request, 'myapp/login.html')

        if not user.is_active:
            messages.error(request, "Your account is blocked. Contact admin.")
            return render(request, 'myapp/login.html')
        
        request.session['user_id'] = user.id
        request.session['user_name'] = user.u_username
        request.session['user_email'] = user.u_email
        request.session['user_role'] = user.role
        request.session['user_pic'] = user.profile_pic.url
        

        if user.role == 'student':
            return redirect('home')
        elif user.role == 'admin':
            return redirect('admin_home')
        elif user.role == 'teacher':
            return redirect('teacher_home')
        else:
            messages.error(request, "User role not assigned")
            return render(request, 'myapp/login.html')

    return render(request, 'myapp/login.html')

@role_requeried(allowed_roles=['student','teacher','admin'])
def home(request):
    user_id = request.session.get('user_id')
    user = reg_model.objects.get(id=user_id)
    
    return render(request,'myapp/home.html',{'user':user})

@role_requeried(allowed_roles=['student','teacher','admin'])
def user_profile(request):
    user_id = request.session.get('user_id')
    user = reg_model.objects.get(id=user_id)


    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            
            user.profile_pic  = request.FILES['profile_pic']
            user.save()
            return redirect('user_profile')


    return render(request,'myapp/user_profile.html',{'user':user})

@role_requeried(allowed_roles=['student','teacher','admin'])


def edit_user(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    user = reg_model.objects.get(id=user_id)

    if request.method == 'POST':
        username = request.POST.get("username", "").strip()
        old_password = request.POST.get("old_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        pic = request.FILES.get('profile_pic')
        

        
        if not username.isalpha():
            return render(request, 'myapp/edit_user.html', {
                'user': user,
                'error': 'Username must contain only letters'
            })

        
        user.u_username = username

        
        if pic:
            user.profile_pic = pic

        if old_password and new_password:
            hashed_password = hashlib.sha256(
            old_password.encode('utf-8')
            ).hexdigest()

            if hashed_password != user.u_password:
                return render(request, 'myapp/edit_user.html', {
                    'user': user,
                    'error': 'Old password is incorrect'
                })

            if old_password == new_password:
                return render(request, 'myapp/edit_user.html', {
                    'user': user,
                    'error': 'New password must be different'
                })
            new_pass = hashlib.sha256(
            new_password.encode('utf-8')
            ).hexdigest()

            user.u_password = new_pass

        user.save()
        return redirect('user_profile')

    return render(request, 'myapp/edit_user.html', {'user': user})

@role_requeried(allowed_roles=['student','teacher','admin'])
def user_course(request):
    courses = course_model.objects.filter(is_active = True)
    return render(request,'myapp/courses.html',{'courses':courses})

@role_requeried(allowed_roles=['student','teacher','admin'])
def enroll_course(request,id):
    course = get_object_or_404(course_model,id=id)
    user_id = request.session.get('user_id')
    user = reg_model.objects.get(id=user_id)
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        
        if user.u_course is None :
            course = get_object_or_404(course_model,id = id)
            user.u_course = course
            user.save()
            subject = f"Enrollment Confirmation for {course.course_name}"
            message = f"Hi {user.u_username},\n\nYou have successfully enrolled in {course.course_name}.\n\nThank you!"
            recipient_list = [user.u_email]
            send_mail(subject, message, None, recipient_list, fail_silently=False)
            messages.success(request,"sucessfully enrolled a course")
            return redirect("user_course")

        else:
            messages.warning(request,"you have already enrolled a course ")
            return redirect('user_course')
        

    return render(request,'myapp/payment.html',{'course':course,'user':user})
     
@role_requeried(allowed_roles=['student','teacher','admin'])
def course_del(request):
    user_id = request.session.get('user_id')
    user = reg_model.objects.get(id = user_id)
    
    if user.u_course is not None:
        user.u_course = None
        user.save()
        subject = f"Course deleting Confirmation for {user.u_course}"
        message = f"Hi {user.u_username},\n\nYou have successfully delete in {user.u_course}.\n\nThank you!"
        recipient_list = [user.u_email]
        send_mail(subject, message, None, recipient_list, fail_silently=False)
    else:
        messages.error(request,"You don't have any courses")
        return redirect('user_profile')
    messages.success(request,'You have successfully deleted the course')
    return redirect('user_profile')

@role_requeried(allowed_roles=['student','teacher','admin'])
def user_logout(request):
    request.session.flush()   
    messages.success(request, "Logged out successfully")
    return redirect('login')



@role_requeried(allowed_roles=['teacher','admin'])
def teacher_home(request):
    return render(request,'myapp/teacher.html')


@role_requeried(allowed_roles=['admin'])
def admin_home(request):
    active_true = course_model.objects.filter(is_active = True).count()
    active_false = course_model.objects.filter(is_active = False).count()
    course_count = course_model.objects.all().count()
    active_course = course_model.objects.filter(is_active = True).count()
    inactive_course = course_model.objects.filter(is_active = False).count()
    inactive_users = reg_model.objects.filter(is_active = False).count()
    students = reg_model.objects.filter(role='student').count()
    teachers = reg_model.objects.filter(role='teacher').count()
    admins = reg_model.objects.filter(role='admin').count()
    total_users  = reg_model.objects.all().count()
    total_profit = reg_model.objects.filter(
    u_course__isnull=False
    ).aggregate(
    total=Sum('u_course__course_price')
            )['total'] or 0
    

    context = {
        'students': students,
        'teachers': teachers,
        'admins': admins,
        "active_true":active_true,
        "active_false":active_false,
        "course_count":course_count,
        "active_course":active_course,
        "total_profit":total_profit,
         "total_users":total_users,
         "inactive_users":inactive_users


    }
    return render(request, 'myapp/admin/admin_home.html', context)
    

@role_requeried(allowed_roles=['admin'])
def add_roles(request):
    students = reg_model.objects.filter(role='student')
    admins = reg_model.objects.filter(role='admin')
    teachers = reg_model.objects.filter(role='teacher')
    no_roles = reg_model.objects.filter(role=None)
   
    return render(request,'myapp/admin/add_role.html',{'students':students,'admins':admins,'teachers':teachers,'no_roles':no_roles})

@role_requeried(allowed_roles=['admin'])
def edit_block(request,id):

    user = reg_model.objects.get(id = id)
    if request.method=="POST":
        user_role = request.POST.get('role')
        if user_role == "none":
            user.role = None
            user.save()
            messages.error(request,"User role set to None")
            return redirect('users_admin')
        else :
            user.role = user_role
            user.save()
            messages.success(request,f"User role set to {user_role} ")
            return redirect("users_admin")
        
        
    return render(request,"myapp/admin/user_page.html",{'user':user})




@role_requeried(allowed_roles=['admin'])
def admin_profile(request):
    admin_id=request.session.get("user_id")
    admin = reg_model.objects.get(id=admin_id)
    return render(request,"myapp/admin/admin_profile.html",{"admin":admin})

@role_requeried(allowed_roles=['admin'])
def admin_edit(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    user = reg_model.objects.get(id=user_id)

    if request.method == 'POST':
        username = request.POST.get("username", "").strip()
        old_password = request.POST.get("old_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        pic = request.FILES.get('profile_pic')
        

        
        if not username.isalpha():
            return render(request, 'myapp/edit_user.html', {
                'user': user,
                'error': 'Username must contain only letters'
            })

        
        user.u_username = username

        
        if pic:
            user.profile_pic = pic

        if old_password and new_password:
            hashed_password = hashlib.sha256(
            old_password.encode('utf-8')
            ).hexdigest()

            if hashed_password != user.u_password:
                return render(request, 'myapp/admin/admin_edit.html', {
                    'user': user,
                    'error': 'Old password is incorrect'
                })

            if old_password == new_password:
                return render(request, 'myapp/admin/admin_edit.html', {
                    'user': user,
                    'error': 'New password must be different'
                })
            new_pass = hashlib.sha256(
            new_password.encode('utf-8')
            ).hexdigest()

            user.u_password = new_pass

        user.save()
        return redirect('admin_profile')

    return render(request, 'myapp/admin/admin_edit.html', {'user': user})
@role_requeried(allowed_roles=['admin'])
def course_admin(request,id):
    user = get_object_or_404(reg_model,id=id)
    if user.u_course is not None:
        user.u_course = None
        user.save()
        subject = f"Course deleting by admin Confirmation for {user.u_course}"
        message = f"Hi {user.u_username},\n\nYou have successfully delete in {user.u_course}.\n\nThank you!"
        recipient_list = [user.u_email]
        send_mail(subject, message, None, recipient_list, fail_silently=False)
    else:
        messages.error(request,"That account don't have any courses")
        return redirect('users_admin')
    messages.success(request,'Course successfully deleted the course')
    return redirect('users_admin')

@role_requeried(allowed_roles=['admin'])
def edit_button(request,id):
    user = get_object_or_404(reg_model,id=id)
    return render(request,"myapp/admin/edit_button.html")

@role_requeried(allowed_roles=['admin'])
def block_button(request,id):
    user = get_object_or_404(reg_model, id=id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request,f"successfully blocked {user.u_username}")
    return redirect("users_admin")

  

@role_requeried(allowed_roles=['admin'])
def active_user(request, id):
    user = get_object_or_404(reg_model, id=id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request,f"successfully unblocked {user.u_username}")
    return redirect("users_admin")


@role_requeried(allowed_roles=['admin'])
def admin_courses(request):

    courses = course_model.objects.all()
    return render(request,"myapp/admin/admin_courses.html",{"courses":courses})
        
@role_requeried(allowed_roles=['admin'])
def course_edit(request,id):
    course = course_model.objects.get(id=id)
    if request.method == "POST":

        course.course_name = request.POST.get('name')
        course.course_price = request.POST.get('price')
        course.course_desc = request.POST.get('bio')
        course.save()
        messages.success(request,"Successfully edited")
        return redirect('admin_courses')
    return render(request,'myapp/admin/course_edit.html',{"course":course})

@role_requeried(allowed_roles=['admin'])
def block_unblock(request,id):
    course = course_model.objects.get(id=id)
    if course.is_active:
        course.is_active = False
        course.save()
        messages.success(request,"Sucessfully blocked")
        return redirect('admin_courses')
    else:
        course.is_active = True
        course.save()
        messages.success(request,"Sucessfully unblocked")
        return redirect('admin_courses')
    
@role_requeried(allowed_roles=['admin'])
def add_new_course(request):
    if request.method == "POST":
        course = course_model.objects.create(
            course_name=request.POST.get('name'),
            course_price=request.POST.get('price'),
            course_desc=request.POST.get('bio')
        )
        messages.success(request,"sucessfully saved the course")
        return redirect("admin_courses")
    return render(request, 'myapp/admin/add_new_course.html')

@role_requeried(allowed_roles=['admin'])
def delete_course(request,id):
    course = course_model.objects.get(id=id)
    course.delete()
    messages.success(request,"successfully deleted")
    return redirect('admin_courses')
    
@role_requeried(allowed_roles=['admin'])
def admin_logout(request):
    request.session.flush()
    return redirect('login')