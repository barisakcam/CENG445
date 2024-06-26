from socket import *
import json
import os
import asyncio
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser

from .forms import *
from .models import User

PHASE2_PORT = 12345
sockets = {}
errorlogs = {}
WS_URI = 'ws://127.0.0.1:1234'
anon_ctr = 0

def socket_send(username, message, receive=False):
    try:
        if username not in sockets:
            sockets[username] = connect(WS_URI)

        s = sockets[username]
        s.send(message)

        if receive:
            response = s.recv(1024 * 16)
            return response
    except ConnectionClosed as e:
        print(e)

def cell_position(context,num):
    WIDTH = 100
    HEIGHT = 100
    rows = (0,0,0,0)
    #print(num)
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
        rows = (2,2,2,2)

    #print(rows)
    x = num*[0] if num>8 else 8*[0]
    y = num*[0] if num>8 else 8*[0]

    x_cur = 0
    y_cur = 0

    i=0
    while i < rows[0]:
        x[i] = x_cur
        y[i] = y_cur
        x_cur += HEIGHT/(rows[0]+1)
        i+=1
    while i < rows[0]+rows[1]:
        x[i] = x_cur
        y[i] = y_cur
        y_cur += WIDTH/(rows[1]+1)
        i+=1
    while i < rows[0]+rows[1]+rows[2]:
        x[i] = x_cur
        y[i] = y_cur
        x_cur -= HEIGHT/(rows[0]+1)
        i+=1
    while i < rows[0]+rows[1]+rows[2]+rows[3]:
        x[i] = x_cur
        y[i] = y_cur
        y_cur -= WIDTH/(rows[1]+1)
        i+=1

    for i in range(num):
        #round to 2 decimal places
        context["board_status"]["cells"][i]["x"] = (x[i]).__round__(2)
        context["board_status"]["cells"][i]["y"] = (y[i]).__round__(2)
        context["board_status"]["cells"][i]["h"] = (HEIGHT/(rows[0]+1)).__round__(2)
        context["board_status"]["cells"][i]["w"] = (WIDTH/(rows[1]+1)).__round__(2)
        context["board_status"]["cells"][i]["namex"] = (x[i] + WIDTH/(rows[1]+1)/2).__round__(2)
        context["board_status"]["cells"][i]["namey"] = (2*y[i]/3 + (y[i] + HEIGHT/(rows[0]+1))/3).__round__(2)
        context["board_status"]["cells"][i]["pricex"] = (x[i] + WIDTH/(rows[1]+1)/2).__round__(2)
        context["board_status"]["cells"][i]["pricey"] = (y[i]/3 + 2*(y[i] + HEIGHT/(rows[0]+1))/3).__round__(2)
        context["board_status"]["cells"][i]["ch"] = (HEIGHT/(rows[0]+1)/2.25).__round__(2)
        context["board_status"]["cells"][i]["userx"] = ((x[i]) + (WIDTH/(rows[1]+1))/4).__round__(2)
        context["board_status"]["cells"][i]["usery"] = (y[i]/4 + 3*(y[i] + HEIGHT/(rows[0]+1))/4).__round__(2)
        context["board_status"]["cells"][i]["userh"] = ((HEIGHT/(rows[0]+1))/4).__round__(2)
        context["board_status"]["cells"][i]["userw"] = ((WIDTH/(rows[1]+1))/2).__round__(2)
        context["board_status"]["cells"][i]["tagx"] = ((x[i]) + (WIDTH/(rows[1]+1))/2).__round__(2)
        context["board_status"]["cells"][i]["tagy"] = ((y[i]) + 9*(HEIGHT/(rows[0]+1))/10).__round__(2)
        context["board_status"]["cells"][i]["levelx"] = ((x[i]) + 5*(WIDTH/(rows[1]+1))/6).__round__(2)
        context["board_status"]["cells"][i]["levely"] = ((y[i]) + (HEIGHT/(rows[0]+1))/6).__round__(2)
        context["board_status"]["cells"][i]["ownerx"] = ((x[i]) + (WIDTH/(rows[1]+1))/4).__round__(2)
        context["board_status"]["cells"][i]["ownery"] = ((y[i]) + (HEIGHT/(rows[0]+1))/6).__round__(2)
    return context

def getName(request):
    if isinstance(request.user, AnonymousUser):
        return request.session['anon_name']
    else:
        return request.user
    
#@login_required(login_url='/login')
def index(request):
    #response = socket_send(getName(request), f"{getName(request)} list", True)
    
    if hasattr(request, 'session') and not request.session.session_key:
        global anon_ctr

        request.session['anon_name'] = 'anon' + str(anon_ctr)
        #request.session.save()
        #request.session.modified = True
        anon_ctr = anon_ctr + 1

    context = {}
    context['boards'] = []#json.loads(response.decode())
    context['username'] = getName(request)

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
            response = socket_send(username, f"{username} login {username} 0", True)

            return redirect('home')
        else:
            context['message']='Invalid username or password'
            return render(request, 'login.html', context)

def register(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context = {}
        context['form'] = RegisterForm()
        context['errors'] = []
        return render(request, 'register/main.html', context)

def registerpost(request):
    if request.user.is_authenticated:
        return redirect("/home")
    else:
        context = {}
        context['form'] = RegisterForm()
        context['errors'] = []

        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        full_name = request.POST["full_name"]

        try:
            user = User.objects.create_user(username, email, password, full_name)
            user.save()
            return redirect('/register/done')
        except IntegrityError as e:
            if 'UNIQUE constraint' in str(e.args):
                if 'username' in str(e.args):
                    context['errors'].append("Username is already used.")
                if 'password' in str(e.args):
                    context['errors'].append("Password is already used.")
                if 'email' in str(e.args):
                    context['errors'].append("Email is already used.")
                if 'full_name' in str(e.args):
                    context['errors'].append("Full name is already used.")
            else:
                print(e)
            return render(request, 'register/main.html', context)
        
def registerdone(request):
    context = {}
    return render(request, 'register/done.html', context)

@login_required(login_url='/login')
def logoutpost(request):

    if getName(request) in sockets:
        socket_send(getName(request), f"{getName(request)} logout", True)
        sockets[getName(request)].close()
        del sockets[getName(request)]
    
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

    if ' ' in request.POST['board_name']:
        context = {}
        context['form'] = BoardAddForm()
        context['errors'] = ['Board name can not include whitespace']
        return render(request, 'board_add.html', context)
    
    with open(filepath, "wb+") as destination:
        for chunk in request.FILES['board_file'].chunks():
            destination.write(chunk)

    if request.POST['board_access'] == 'owner':
        access_list = [request.user.username]
    elif request.POST['board_access'] == 'select_users':
        access_list = request.POST.getlist('board_users')
    elif request.POST['board_access'] == 'authenticated':
        access_list = []
    elif request.POST['board_access'] == 'all':
        access_list = ['anon']

    access_list_str = json.dumps(access_list, separators=(',', ':'))

    response = socket_send(getName(request), f"{getName(request)} new {request.POST['board_name']} ../board_files/{request.FILES['board_file']} {request.POST['board_access']} {access_list_str}", True)
    errorlogs[request.POST['board_name']] = []

    return redirect("/home")

#@login_required(login_url='/login')
def board_view(request, boardname):
    context = {}
    
    response = socket_send(getName(request), f"{getName(request)} login {getName(request)} 0", True)
    response = socket_send(getName(request), f"{getName(request)} boardinfo {boardname}", True)

    context["board_name"] = boardname
    context["board_status"] = json.loads(response)
    context["command_form"] = CommandForm()

    if boardname not in errorlogs:
        errorlogs[boardname] = []

    response = socket_send(getName(request), f"{getName(request)} gamelog", True)
    context["game_log"] = response.split("\n")
    context["error_log"] = errorlogs[boardname]

    context = cell_position(context, len(context["board_status"]["cells"]))

    context["username"] = getName(request)

    return render(request, 'board.html', context)

#@login_required(login_url='/login')
def board_open(request, boardname):
    response = socket_send(getName(request), f"{getName(request)} login {getName(request)} 0", True)
    response = socket_send(getName(request), f"{getName(request)} close", True) # to make browser back button work
    response = socket_send(getName(request), f"{getName(request)} open {boardname}", True)

    return redirect(f"/board/{boardname}/")

#@login_required(login_url='/login')
def board_close(request, boardname):
    response = socket_send(getName(request), f"{getName(request)} close", True)

    return redirect("/home")

#@login_required(login_url='/login')
def board_ready(request, boardname):
    response = socket_send(getName(request), f"{getName(request)} ready", True)

    return redirect(f"/board/{boardname}/")

#@login_required(login_url='/login')
def board_refresh(request, boardname):
    return redirect(f"/board/{boardname}/")

#@login_required(login_url='/login')
def board_command(request, boardname):
    if request.POST['command_name'] == "teleport" or request.POST['command_name'] == "pick":
        response = socket_send(getName(request), f"{getName(request)} {request.POST['command_name']} {request.POST['command_argument']}", True)
    else:
        response = socket_send(getName(request), f"{getName(request)} {request.POST['command_name']}", True)

    if boardname in errorlogs:
        errorlogs[boardname].append(response.split('\n'))
    else:
        errorlogs[boardname] = response.split('\n')

    if response != "SUCCESS":
        print(response)
        
    return redirect(f"/board/{boardname}/")
