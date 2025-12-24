"""
账户应用的单元测试
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordChangeForm


class CustomUserCreationFormTest(TestCase):
    """自定义用户注册表单测试"""
    
    def test_valid_registration_form(self):
        """测试有效的注册表单"""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """测试密码不匹配"""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'differentpass'
        })
        self.assertFalse(form.is_valid())
    
    def test_username_required(self):
        """测试用户名必填"""
        form = CustomUserCreationForm(data={
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertFalse(form.is_valid())
    
    def test_password_too_short(self):
        """测试密码太短"""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'password1': 'short',
            'password2': 'short'
        })
        self.assertFalse(form.is_valid())


class RegistrationViewTest(TestCase):
    """注册视图测试"""
    
    def setUp(self):
        """设置测试客户端"""
        self.client = Client()
    
    def test_register_view_get(self):
        """测试注册页面 GET 请求"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
    
    def test_register_view_post_success(self):
        """测试注册成功"""
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'newuser',
                'password1': 'testpass123',
                'password2': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_view_post_failure(self):
        """测试注册失败"""
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'newuser',
                'password1': 'testpass123',
                'password2': 'differentpass'
            }
        )
        self.assertEqual(response.status_code, 200)  # 返回表单页面
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginViewTest(TestCase):
    """登录视图测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login_view_get(self):
        """测试登录页面 GET 请求"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_login_view_post_success(self):
        """测试登录成功"""
        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_post_failure(self):
        """测试登录失败"""
        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': 'testuser',
                'password': 'wrongpassword'
            }
        )
        self.assertEqual(response.status_code, 200)  # 返回登录页面
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ProfileViewTest(TestCase):
    """用户资料视图测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_profile_view_requires_login(self):
        """测试资料页面需要登录"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页
    
    def test_profile_view_authenticated(self):
        """测试已登录用户访问资料页面"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/profile.html')
        self.assertEqual(response.context['user'], self.user)
