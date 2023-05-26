from django import forms

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

    board_name = forms.CharField(max_length=16)
    board_file = forms.FileField()

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