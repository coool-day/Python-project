"""Defines URL patterns for accounts."""

from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views


app_name = 'accounts'
urlpatterns = [
    # 登录页面（使用自定义视图）
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # 退出登录
    path('logout/', LogoutView.as_view(), name='logout'),
    # 注册页面
    path('register/', views.register, name='register'),
    # 用户资料
    path('profile/', views.profile, name='profile'),
    # 修改密码
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]