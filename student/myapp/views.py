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

            return HttpResponse("link sented")
        else:
            return render(request, 'myapp/register.html', {'form': form})
    else:
        form = reg_form()
        return render(request, 'myapp/register.html', {'form': form})
    

def activate_account(request,token):
   user=get_object_or_404(reg_model,activation_token = token)
   if user.role == None:
       user.role='student'
       user.activation_token = None
       user.save()
       return HttpResponse("activation successful")
   else:
       return HttpResponse("account already activated")
       


def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        hashed_password = hashlib.sha256(
            password.encode('utf-8')
        ).hexdigest()

        obj = reg_model.objects.filter(Q(u_email = email) & Q(u_password = hashed_password))
        if obj.exists():
            user = obj.first()
            request.session['user_id']=user.id
            request.session['user_name']=user.u_username
            request.session['user_email']=user.u_email
            request.session['user_pic']=user.profile_pic.url
            request.session['user_role']=user.role
            if user.role == 'student':
               return redirect('home')
            elif user.role == 'admin':
               return redirect('admin_home')
            else :
               return redirect('teacher_home') 

        else:
            return render(request,'myapp/login.html',{'error' : 'invalid email or password'})


    return render(request,'myapp/login.html')

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
    user = reg_model.objects.get(id = user_id)
    if request.method == 'POST':
        username = request.POST.get("username")
        if username.isalpha():
            user.u_username = username
            user.profile_pic = request.FILES['profile_pic']
            user.save()
            return redirect ('user_profile')
        else:
            return render(request,'myappp/edit_user.html',{'user':user , 'error':'user name must have alphabet '})
    return render(request,'myapp/edit_user.html',{'user':user})

@role_requeried(allowed_roles=['student','teacher','admin'])
def user_course(request):
    
    courses = course_model.objects.all()
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
        else:
            messages.warning(request,"you have already enrolled a course ")
            return redirect('user_course')
        messages.success(request,"sucessfully enrolled a course")
        return redirect("user_course")

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

def user_logout(request):
    request.session.flush()   
    messages.success(request, "Logged out successfully")
    return redirect('login')



@role_requeried(allowed_roles=['teacher','admin'])
def teacher_home(request):
    return render(request,'myapp/teacher.html')


@role_requeried(allowed_roles=['admin'])
def admin_home(request):
    return render(request,'myapp/admin/admin_home.html')

def add_roles(request):
    return HttpResponse("role page")

