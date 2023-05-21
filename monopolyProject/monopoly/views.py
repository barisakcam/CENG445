from socket import *
import json
import os

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from .forms import *
from .models import User

PHASE2_PORT = 1233
sockets = {}

def socket_send(username, message):
    if username not in sockets:
        sockets[username] = socket(AF_INET, SOCK_STREAM)
        sockets[username].connect(('', PHASE2_PORT))

    s = sockets[username]
    s.send(message.encode())
    response = s.recv(1024 * 16)
    return response

def cell_position(context,num):
    WIDTH = 1000
    HEIGHT = 800
    rows = (0,0,0,0)
    print(num)
    if num>=8:
        if num%4 == 0:
            rows = (num//4,num//4,num//4,num//4)
        elif num%4 == 1:
            rows = (num//4,num//4+1,num//4,num//4)
        elif num%4 == 2:
            rows = (num//4,num//4+1,num//4,num//4+1)
        elif num%4 == 3:
            rows = (num//4+1,num//4+1,num//4+1,num//4)
    else:
        rows = (0,num,0,0)

    print(rows)
    x = num*[0]
    y = num*[0]

    x_cur = 0
    y_cur = 0

    i=0
    while i < rows[0]:
        x[i] = x_cur
        y[i] = y_cur
        y_cur += HEIGHT/(rows[0]+1)
        i+=1
    while i < rows[0]+rows[1]:
        x[i] = x_cur
        y[i] = y_cur
        x_cur += WIDTH/(rows[1]+1)
        i+=1
    while i < rows[0]+rows[1]+rows[2]:
        x[i] = x_cur
        y[i] = y_cur
        y_cur -= HEIGHT/(rows[0]+1)
        i+=1
    while i < rows[0]+rows[1]+rows[2]+rows[3]:
        x[i] = x_cur
        y[i] = y_cur
        x_cur -= WIDTH/(rows[1]+1)
        i+=1

    for i in range(num):
        context["board_status"]["cells"][i]["x"] = int(x[i])
        context["board_status"]["cells"][i]["y"] = int(y[i])
        context["board_status"]["cells"][i]["h"] = int(HEIGHT/(rows[0]+1))
        context["board_status"]["cells"][i]["w"] = int(WIDTH/(rows[1]+1))
        context["board_status"]["cells"][i]["namex"] = int(x[i] + WIDTH/(rows[1]+1)/2)
        context["board_status"]["cells"][i]["namey"] = int(2*y[i]/3 + (y[i] + HEIGHT/(rows[0]+1))/3)
        context["board_status"]["cells"][i]["pricex"] = int(x[i] + WIDTH/(rows[1]+1)/2)
        context["board_status"]["cells"][i]["pricey"] = int(y[i]/3 + 2*(y[i] + HEIGHT/(rows[0]+1))/3)
        context["board_status"]["cells"][i]["ch"] = int(HEIGHT/(rows[0]+1)/2.25)
    return context

@login_required(login_url='/login')
def index(request):
    response = socket_send(request.user.username, f"{request.user.username} list")

    context = {}
    context['boards'] = json.loads(response.decode())

    return render(request,'board_list.html', context)

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
            return redirect("/home")

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

    if request.user.username in sockets:
        response = socket_send(request.user.username, f"{request.user.username} logout")
        sockets[request.user.username].close()
        del sockets[request.user.username]
    
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

    with open(filepath, "wb+") as destination:
        for chunk in request.FILES['board_file'].chunks():
            destination.write(chunk)

    socket_send(request.user.username, f"{request.user.username} new {request.POST['board_name']} ../board_files/{request.FILES['board_file']}")
    
    return redirect("/home")

@login_required(login_url='/login')
def board_view(request, boardname):
    context ={}

    response = socket_send(request.user.username, f"{request.user.username} login {request.user.username} 0")
    response = socket_send(request.user.username, f"{request.user.username} boardinfo {boardname}")
    
    context["board_name"] = boardname
    context["board_status"] = json.loads(response.decode())
    context["command_form"] = CommandForm()

    context = cell_position(context, len(context["board_status"]["cells"]))

    print(context["board_status"])
    return render(request, 'board.html', context)


@login_required(login_url='/login')
def board_open(request, boardname):
    response = socket_send(request.user.username, f"{request.user.username} login {request.user.username} 0")
    response = socket_send(request.user.username, f"{request.user.username} close") # to make browser back button work
    response = socket_send(request.user.username, f"{request.user.username} open {boardname}")

    return redirect(f"/board/{boardname}/")

@login_required(login_url='/login')
def board_close(request, boardname):
    response = socket_send(request.user.username, f"{request.user.username} close")

    return redirect("/home")

@login_required(login_url='/login')
def board_ready(request, boardname):
    response = socket_send(request.user.username, f"{request.user.username} ready")

    return redirect(f"/board/{boardname}/")

@login_required(login_url='/login')
def board_command(request, boardname):
    print(request.POST)
    #response = socket_send(request.user.username, f"{request.user.username} ready")

    return redirect(f"/board/{boardname}/")
