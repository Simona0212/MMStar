"""
URL configuration for mmstar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static
# from django.urls import re_path as url
# from django.views import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", user_views.home, name="home"),
    path("register/", user_views.register, name="register"),
    path("login/", user_views.login_view, name="login"),
    path("logout/", user_views.logout_view, name="logout"),
    path("", include("users.urls")),  # 包含 users 应用的所有 URL 配置
    path("teacher/", include("users.urls")),
    path("student/", include("users.urls")),
    path("administrator/", include("users.urls")),
]

if settings.DEBUG:  # 仅在 DEBUG 为 True 时才添加此项，用于开发环境下的静态文件访问
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
