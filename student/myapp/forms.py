from django import forms
from .models import reg_model
class reg_form(forms.ModelForm):
    class Meta:
        model = reg_model
        fields = ['u_username','u_email','u_password','u_confirm','profile_pic']
        widgets = {
            'u_username' : forms.TextInput(attrs={
                'class':'input_field',
                'placeholder':'Enter your name'
            }),
            'u_email': forms.EmailInput(attrs={
                'class':'input_field',
                'placeholder':'Enter your email'
            }),
            'u_password': forms.PasswordInput(attrs={
                'class':'input_field',
                'placeholder':'Enter your password',
                
            }),
            'u_confirm': forms.PasswordInput(attrs={
                'class':'input_field',
                'placeholder':'Confirm password',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        ps1 = cleaned_data.get('u_password')
        ps2 = cleaned_data.get('u_confirm')
        if ps1 and len(ps1) < 4 :
                self.add_error('u_password','password length must want 4 or more letters')

        if ps1 and ps2 and ps1 != ps2 : 
                
            self.add_error('u_password','password dont match')
        return cleaned_data
    
    def clean_u_email(self):
        email = self.cleaned_data.get('u_email')
        if reg_model.objects.filter(u_email = email).exists():
            self.add_error('u_email',"email already exist")
        return email
    def clean_u_username(self):
        username = self.cleaned_data.get('u_username')
        if username and not username.isalpha():
            self.add_error('u_username',"username only contains letters")
        return username
