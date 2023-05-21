"""monopolyProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url, include
from django.shortcuts import redirect

import monopoly.views

urlpatterns = [
    url(r'admin/', admin.site.urls),
    url(r'$', lambda _: redirect('/home')),
    url(r'home/$', monopoly.views.index, name='home'),
    url(r'login/$', monopoly.views.login_view, name='login'),
    url(r'loginpost/$', monopoly.views.login_post, name='login_post'),
    url(r'register/$', monopoly.views.register, name='register'),
    url(r'registerpost/$', monopoly.views.registerpost, name='registerpost'),
    url(r'logout/$', monopoly.views.logoutpost, name='logout'),
    url(r'board/add/$', monopoly.views.board_add_view, name='board_add'),
    url(r'board/addpost/$', monopoly.views.board_add_post, name='board_add_post'),
    url(r'board/([a-zA-Z0-9]+)/$', monopoly.views.board_view, name='board_view'),
    url(r'board/([a-zA-Z0-9]+)/open$', monopoly.views.board_open, name='board_open'),
    url(r'board/([a-zA-Z0-9]+)/close/$', monopoly.views.board_close, name='board_close'),
    url(r'board/([a-zA-Z0-9]+)/ready/$', monopoly.views.board_ready, name='board_ready'),
    url(r'board/([a-zA-Z0-9]+)/refresh/$', monopoly.views.board_refresh, name='board_refresh'),
    url(r'board/([a-zA-Z0-9]+)/command/$', monopoly.views.board_command, name='board_command'),
    #url('accounts/', include('django.contrib.auth.urls')),
]
