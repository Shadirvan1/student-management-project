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
        

