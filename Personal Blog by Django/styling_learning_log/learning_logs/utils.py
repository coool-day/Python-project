"""
工具函数和装饰器
"""
from functools import wraps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect


def handle_view_exceptions(view_func):
    """
    统一处理视图异常的装饰器
    自动捕获常见异常并显示友好的错误消息
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except PermissionDenied as e:
            messages.error(request, f'❌ 权限不足：{str(e)}')
            return redirect('learning_logs:topics')
        except Http404:
            messages.error(request, '❌ 未找到请求的资源。')
            return redirect('learning_logs:topics')
        except Exception as e:
            # 记录详细错误信息（生产环境应使用日志系统）
            messages.error(request, f'❌ 发生错误：{str(e)}')
            return redirect('learning_logs:topics')
    return wrapper


def check_topic_owner(topic, user):
    """
    检查主题是否属于指定用户
    如果不属于，抛出 PermissionDenied 异常
    """
    if topic.owner != user:
        raise PermissionDenied("您没有权限访问此主题。")
    return True


def check_entry_owner(entry, user):
    """
    检查条目所属的主题是否属于指定用户
    如果不属于，抛出 PermissionDenied 异常
    """
    if entry.topic.owner != user:
        raise PermissionDenied("您没有权限访问此条目。")
    return True

