import hashlib
from django.shortcuts import render,redirect
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
# Create your views here.
from .forms import reg_form
from .models import reg_model
from django.db.models import Q
from .decorators import role_requeried

def register_page(request):
    if request.method == 'POST':
        form = reg_form(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            raw_pass = form.cleaned_data['u_password']
            user.u_password = hashlib.sha256(
                raw_pass.encode('utf-8')
            ).hexdigest()
            user.u_confirm = ''
            user.save()
            return redirect('')
        else:
            return render(request,'myapp/register.html',{'form':form})
    else:  
        form = reg_form()
        return render(request,'myapp/register.html',{'form':form})


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
    
    return HttpResponse("helll")


@role_requeried(allowed_roles=['teacher','admin'])
def teacher_home(request):
    return render(request,'myapp/teacher.html')


@role_requeried(allowed_roles=['admin'])
def admin_home(request):
    return render(request,'myapp/admin_home.html')

