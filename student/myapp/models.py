from django.db import models

# Create your models here.

class course_model(models.Model):
    course_name = models.CharField(max_length=30)
    course_desc = models.TextField()
    course_price = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__ (self):
        return self.course_name

class reg_model(models.Model):

    role_choices = (
        ('student','Student'),
        ('teacher','Teacher'),
        ('admin','Admin'),
    )
    u_username = models.CharField(max_length=30)
    u_email = models.EmailField(max_length=30,unique=True)
    u_password = models.CharField()
    u_confirm = models.CharField(null=True,blank=True)
    
    role = models.CharField(max_length=20,choices=role_choices,null=True,blank=True,default=None)

    def __str__(self):
        return self.u_username
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default.png',
        blank=True,
        null=True
    )

    u_course = models.ForeignKey(course_model,
        on_delete=models.SET_NULL,blank=True,null = True)
    activation_token = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    pre_role = models.CharField(default=None,blank=True,null=True)


