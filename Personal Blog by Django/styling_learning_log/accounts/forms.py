from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_text_html
)


class CustomUserCreationForm(UserCreationForm):
    """自定义用户注册表单，使用中文标签和提示"""
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        labels = {
            'username': '用户名',
            'password1': '密码',
            'password2': '确认密码',
        }
        help_texts = {
            'username': '必填。150个字符或更少。只能包含字母、数字和 @/./+/-/_ 字符。',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段标签
        self.fields['username'].label = '用户名'
        self.fields['password1'].label = '密码'
        self.fields['password2'].label = '确认密码'
        
        # 设置帮助文本
        self.fields['username'].help_text = '必填。150个字符或更少。只能包含字母、数字和 @/./+/-/_ 字符。'
        self.fields['password1'].help_text = self._get_password_help_text()
        self.fields['password2'].help_text = '请再次输入相同的密码以进行验证。'
        
        # 设置占位符
        self.fields['username'].widget.attrs.update({
            'placeholder': '请输入用户名',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': '请输入密码',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': '请再次输入密码',
            'class': 'form-control'
        })
        
        # 自定义错误消息
        self.fields['username'].error_messages = {
            'required': '请输入用户名。',
            'unique': '该用户名已被使用，请选择其他用户名。',
        }
        self.fields['password1'].error_messages = {
            'required': '请输入密码。',
        }
        self.fields['password2'].error_messages = {
            'required': '请确认密码。',
        }
    
    def _get_password_help_text(self):
        """获取密码要求的中文帮助文本"""
        help_texts = [
            '• 密码不能与您的其他个人信息过于相似。',
            '• 密码必须包含至少8个字符。',
            '• 密码不能是常用的密码。',
            '• 密码不能完全是数字。',
        ]
        return '<br>'.join(help_texts)
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            # 验证密码并捕获错误，转换为中文消息
            try:
                validate_password(password1, self.instance)
            except forms.ValidationError as e:
                # 将英文错误消息转换为中文
                new_errors = []
                for error in e.messages:
                    error_lower = error.lower()
                    if 'too short' in error_lower:
                        import re
                        match = re.search(r'(\d+)', error)
                        if match:
                            new_errors.append(f'密码太短，必须包含至少{match.group(1)}个字符。')
                        else:
                            new_errors.append('密码太短，必须包含至少8个字符。')
                    elif 'too common' in error_lower:
                        new_errors.append('密码太常见，请使用更复杂的密码。')
                    elif 'entirely numeric' in error_lower:
                        new_errors.append('密码不能完全是数字。')
                    elif 'too similar' in error_lower:
                        new_errors.append('密码与您的其他个人信息过于相似。')
                    else:
                        # 保留原始错误消息（如果无法转换）
                        new_errors.append(error)
                
                if new_errors:
                    raise forms.ValidationError(new_errors)
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "两次输入的密码不匹配，请重新输入。",
                code='password_mismatch',
            )
        return password2


class CustomAuthenticationForm(AuthenticationForm):
    """自定义用户登录表单，使用中文标签"""
    
    error_messages = {
        'invalid_login': '请输入正确的用户名和密码。注意：密码区分大小写。',
        'inactive': '此账户已被停用。',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段标签
        self.fields['username'].label = '用户名'
        self.fields['password'].label = '密码'
        
        # 设置占位符
        self.fields['username'].widget.attrs.update({
            'placeholder': '请输入用户名',
            'class': 'form-control'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': '请输入密码',
            'class': 'form-control'
        })
        
        # 设置错误消息
        self.fields['username'].error_messages = {
            'required': '请输入用户名。',
        }
        self.fields['password'].error_messages = {
            'required': '请输入密码。',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """自定义密码修改表单，使用中文标签"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段标签
        self.fields['old_password'].label = '当前密码'
        self.fields['new_password1'].label = '新密码'
        self.fields['new_password2'].label = '确认新密码'
        
        # 设置占位符
        self.fields['old_password'].widget.attrs.update({
            'placeholder': '请输入当前密码',
            'class': 'form-control'
        })
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': '请输入新密码',
            'class': 'form-control'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': '请再次输入新密码',
            'class': 'form-control'
        })
        
        # 设置帮助文本
        self.fields['new_password1'].help_text = self._get_password_help_text()
    
    def _get_password_help_text(self):
        """获取密码要求的中文帮助文本"""
        help_texts = [
            '• 密码不能与您的其他个人信息过于相似。',
            '• 密码必须包含至少8个字符。',
            '• 密码不能是常用的密码。',
            '• 密码不能完全是数字。',
        ]
        return '<br>'.join(help_texts)

