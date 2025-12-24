from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

def role_requeried(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request,*args,**kwargs):
            user_role = request.session.get('user_role')
            if not user_role :
                return redirect('login')
            if user_role in allowed_roles:
                return view_func(request,*args,**kwargs)
            else:
                return HttpResponse("access denied : you do not have permission to view this page")
        return wrapper
    return decorator
          

def check_reg(view_func):
    def wrapper(request,*args,**kwargs):
        role = request.session.get('user_role')
        if request.session.get('user_id'):
            if role == "student":
                return redirect("home")
            elif role == "admin":
                return redirect("admin_home")
            else:
                return redirect("register")
        return view_func(request,*args,**kwargs)
    return wrapper