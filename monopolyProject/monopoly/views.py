from socket import *
import json
import os

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from .forms import *
from .models import User

PHASE2_PORT=1234

@login_required(login_url='/login')
def index(request):
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('', PHASE2_PORT))
    s.send(f"{request.user.username} list".encode())
    response = s.recv(1024)
    s.close()

    print(response.decode())
    print(json.loads(response.decode()))

    return render(request,'board.html',{'boards': json.loads(response.decode())})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context ={}
        context['form']= LoginForm()

        return render(request, 'login.html', context)

def login_post(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context ={}
        context['form']= LoginForm()

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context['message']='Invalid username or password'
            #return redirect("/home")
            return render(request, 'login.html', context)

def register(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context ={}
        context['form']= RegisterForm()
        return render(request, 'register.html', context)

def registerpost(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context ={}
        context['form'] = RegisterForm()

        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        full_name = request.POST["full_name"]

        user = User.objects.create_user(username, email, password, full_name)
        user.save()

        return render(request, 'register.html', context)

@login_required(login_url='/login')
def logoutpost(request):
	logout(request)
	return redirect("/home")

@login_required(login_url='/login')
def board_add_view(request):
    context ={}
    context['form'] = BoardAddForm()
    return render(request, 'board_add.html', context)

@login_required(login_url='/login')
def board_add_post(request):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, f"board_files/{request.FILES['board_file']}")
    #print(os.path.exists(filepath))

    with open(filepath, "wb+") as destination:
        for chunk in request.FILES['board_file'].chunks():
            destination.write(chunk)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('', PHASE2_PORT))
    s.send(f"{request.user.username} new {request.POST['board_name']} ../board_files/{request.FILES['board_file']}".encode())
    s.close()
    
    return redirect("/home")