from django.db import models

# Create your models here.


class reg_model(models.Model):

    role_choices = (
        ('student','Student'),
        ('teacher','Teacher'),
        ('admin','Admin'),
    )
    u_username = models.CharField(max_length=30,unique=True)
    u_email = models.EmailField(max_length=30,unique=True)
    u_password = models.CharField()
    u_confirm = models.CharField(null=True,blank=True)
    
    role = models.CharField(max_length=20,choices=role_choices,default='student')

    def __str__(self):
        return self.u_username