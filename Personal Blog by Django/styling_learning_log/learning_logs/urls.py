"""Defines URL patterns for learning_logs."""

from django.urls import path

from . import views
from . import health

app_name = 'learning_logs'
urlpatterns = [
    # 首页
    path('', views.index, name='index'),
    # 显示所有主题
    path('topics/', views.topics, name='topics'),
    # 显示单个主题详情
    path('topics/<int:topic_id>/', views.topic, name='topic'),
    # 添加新主题
    path('new_topic/', views.new_topic, name='new_topic'),
    # 添加新笔记
    path('new_entry/<int:topic_id>/', views.new_entry, name='new_entry'),
    # 编辑笔记
    path('edit_entry/<int:entry_id>/', views.edit_entry, name='edit_entry'),
    # 删除主题
    path('delete_topic/<int:topic_id>/', views.delete_topic, name='delete_topic'),
    # 删除笔记
    path('delete_entry/<int:entry_id>/', views.delete_entry, name='delete_entry'),
    # 数据统计
    path('statistics/', views.statistics, name='statistics'),
    # 导出数据
    path('export/<str:format_type>/', views.export_data, name='export_data'),
    # 健康检查端点
    path('health/', health.health_check, name='health_check'),
    path('health/detailed/', health.health_check_detailed, name='health_check_detailed'),
    path('health/ready/', health.readiness_check, name='readiness_check'),
    path('health/live/', health.liveness_check, name='liveness_check'),
]