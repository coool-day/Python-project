"""
学习笔记自定义模板标签
"""
from django import template
import markdown

register = template.Library()


@register.filter(name='markdown')
def markdown_filter(text):
    """
    将 Markdown 文本转换为 HTML
    """
    if not text:
        return ''
    return markdown.markdown(text, extensions=['extra', 'codehilite'])


@register.filter(name='split')
def split_filter(value, arg):
    """
    分割字符串
    用法: {{ value|split:"," }}
    """
    if not value:
        return []
    return value.split(arg)


@register.filter(name='trim')
def trim_filter(value):
    """
    去除字符串首尾空格
    """
    if not value:
        return ''
    return value.strip()


@register.simple_tag
def topic_color_class(color):
    """
    根据主题颜色返回 Bootstrap 颜色类
    """
    color_map = {
        'primary': 'primary',
        'success': 'success',
        'warning': 'warning',
        'danger': 'danger',
        'info': 'info',
        'secondary': 'secondary',
        'dark': 'dark',
    }
    return color_map.get(color, 'primary')

