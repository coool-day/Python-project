#!/usr/bin/env python
"""检查 Django 设置 - 用于诊断 SSL 问题"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'll_project.settings')
django.setup()

from django.conf import settings

print("=" * 50)
print("Django 设置检查")
print("=" * 50)
print(f"DEBUG: {settings.DEBUG}")
print(f"SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', 'Not set')}")
print(f"SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', 'Not set')}")
print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', 'Not set')}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print("=" * 50)

if settings.DEBUG:
    print("✅ DEBUG 模式已启用，SSL 重定向应该被禁用")
    print("✅ 如果浏览器仍显示 SSL 错误，请清除浏览器缓存")
else:
    print("⚠️  DEBUG 模式未启用，SSL 重定向可能已启用")
    print("⚠️  请在 .env 文件中设置 DEBUG=True")

