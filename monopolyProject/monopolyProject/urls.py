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

import monopoly.views

urlpatterns = [
    url('admin/', admin.site.urls),
    url('home/', monopoly.views.index, name='home'),
    url('login/', monopoly.views.login_view, name='login'),
    url('loginpost/', monopoly.views.login_post, name='login_post'),
    url('register/', monopoly.views.register, name='register'),
    url('registerpost/', monopoly.views.registerpost, name='registerpost'),
    url('logout/', monopoly.views.logoutpost, name='logout'),
    url('board/add/', monopoly.views.board_add_view, name='board_add'),
    url('board/addpost/', monopoly.views.board_add_post, name='board_add_post'),
    #url('accounts/', include('django.contrib.auth.urls')),
]
