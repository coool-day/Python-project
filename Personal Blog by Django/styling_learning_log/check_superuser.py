#!/usr/bin/env python
"""检查和管理 Django 超级用户的脚本"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'll_project.settings')
django.setup()

from django.contrib.auth.models import User

print("=" * 50)
print("Django 超级用户检查工具")
print("=" * 50)

# 检查所有超级用户
superusers = User.objects.filter(is_superuser=True)

if superusers.exists():
    print(f"\n✅ 找到 {superusers.count()} 个超级用户：\n")
    for u in superusers:
        print(f"  用户名: {u.username}")
        print(f"  邮箱: {u.email or '(未设置)'}")
        print(f"  最后登录: {u.last_login or '(从未登录)'}")
        print(f"  注册时间: {u.date_joined}")
        print("-" * 50)
else:
    print("\n❌ 未找到超级用户！")
    print("\n请运行以下命令创建超级用户：")
    print("  python manage.py createsuperuser")

print("\n" + "=" * 50)
print("⚠️  注意：Django 密码是加密存储的，无法直接查看原始密码。")
print("如果忘记密码，可以使用以下方法重置：")
print("=" * 50)
print("\n方法 1：使用 Django shell 重置密码")
print("  python manage.py shell")
print("  然后执行：")
print("  from django.contrib.auth.models import User")
print("  u = User.objects.get(username='你的用户名')")
print("  u.set_password('新密码')")
print("  u.save()")
print("\n方法 2：使用 changepassword 命令")
print("  python manage.py changepassword 用户名")
print("=" * 50)

