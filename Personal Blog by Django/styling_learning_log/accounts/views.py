from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordChangeForm


def register(request):
    """
    用户注册视图
    
    功能：
    - GET: 显示注册表单
    - POST: 处理注册表单提交
    - 注册成功后自动登录用户
    - 表单验证和错误处理
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse:
            - GET: 渲染注册表单
            - POST: 成功则重定向到首页，失败则显示表单和错误
    """
    if request.method != 'POST':
        # 显示空白注册表单
        form = CustomUserCreationForm()
    else:
        # 处理已提交的表单
        form = CustomUserCreationForm(data=request.POST)

        if form.is_valid():
            new_user = form.save()
            # 登录用户并重定向到首页
            login(request, new_user)
            return redirect('learning_logs:index')

    # 显示空白或无效的表单
    context = {'form': form}
    return render(request, 'registration/register.html', context)


class CustomLoginView(LoginView):
    """
    自定义登录视图
    
    功能：
    - 使用中文表单和错误消息
    - 已登录用户自动重定向
    - 自定义错误消息处理
    
    属性:
        form_class: 使用的表单类（CustomAuthenticationForm）
        template_name: 模板文件路径
        redirect_authenticated_user: 已登录用户是否重定向
    """
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def form_invalid(self, form):
        # 自定义错误消息为中文
        response = super().form_invalid(form)
        if form.errors:
            # 将常见的登录错误消息转换为中文
            if '__all__' in form.errors:
                for i, error in enumerate(form.errors['__all__']):
                    if 'Please enter a correct username and password' in str(error) or 'Invalid login' in str(error):
                        form.errors['__all__'][i] = '用户名或密码错误，请重试。'
        return response


@login_required
def profile(request):
    """
    用户资料页面视图
    
    功能：
    - 显示用户基本信息（用户名、邮箱、注册时间等）
    - 显示学习统计（主题数、笔记数）
    - 提供快速链接（查看统计、修改密码）
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 渲染的用户资料页面模板
    """
    user = request.user
    # 统计用户的学习数据
    from learning_logs.models import Topic, Entry
    topics_count = Topic.objects.filter(owner=user).count()
    entries_count = Entry.objects.filter(topic__owner=user).count()
    
    context = {
        'user': user,
        'topics_count': topics_count,
        'entries_count': entries_count,
        'date_joined': user.date_joined,
    }
    return render(request, 'registration/profile.html', context)


class CustomPasswordChangeView(PasswordChangeView):
    """
    自定义密码修改视图
    
    功能：
    - 使用中文表单和错误消息
    - 修改成功后显示成功消息
    - 重定向到用户资料页面
    
    属性:
        form_class: 使用的表单类（CustomPasswordChangeForm）
        template_name: 模板文件路径
        success_url: 成功后的重定向URL
    """
    form_class = CustomPasswordChangeForm
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        messages.success(self.request, '✅ 密码已成功修改！')
        return super().form_valid(form)