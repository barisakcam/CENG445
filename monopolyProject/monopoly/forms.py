from django import forms
from .models import User

# login.html
class LoginForm(forms.Form):
  
    username = forms.CharField(max_length=16)
    password = forms.CharField(widget = forms.PasswordInput())

# register.html
class RegisterForm(forms.Form):
  
    username = forms.CharField(max_length=16)
    password = forms.CharField(widget = forms.PasswordInput(), max_length=16)
    email = forms.EmailField()
    full_name = forms.CharField(max_length=32)

class BoardAddForm(forms.Form):
    share_choices = (('owner', 'owner'),
                     ('select_users', 'select users'),
                     ('authenticated', 'authenticated'),
                     ('all', 'all'))
    user_choices = [(user.username, user.username) for user in User.objects.all()]
    board_name = forms.CharField(max_length=16)
    board_file = forms.FileField()
    board_access = forms.ChoiceField(choices=share_choices)
    board_users = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=user_choices)

class CommandForm(forms.Form):
    
    choices = (('roll', 'roll'),
               ('buy', 'buy'),
               ('upgrade', 'upgrade'),
               ('teleport', 'teleport'),
               ('pick', 'pick'),
               ('bail', 'bail'),
               ('end', 'end'),)
    
    command_name = forms.ChoiceField(choices=choices)

    command_argument = forms.CharField(widget=forms.NumberInput(), required=False)