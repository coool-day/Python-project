"""
健康检查端点

用于监控系统状态，包括：
- 基本健康检查
- 数据库连接检查
- 缓存连接检查
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    基本健康检查端点
    
    返回：
        JsonResponse: 包含系统状态的 JSON 响应
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'learning_log',
        'version': '1.0.0',
    })


def health_check_detailed(request):
    """
    详细健康检查端点
    
    检查：
    - 数据库连接
    - 缓存连接
    - 静态文件配置
    
    返回：
        JsonResponse: 包含详细系统状态的 JSON 响应
    """
    checks = {
        'status': 'healthy',
        'service': 'learning_log',
        'version': '1.0.0',
        'checks': {}
    }
    
    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
    except Exception as e:
        logger.error(f'Database health check failed: {str(e)}')
        checks['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        checks['status'] = 'unhealthy'
    
    # 检查缓存连接
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 10)
        cache_value = cache.get(cache_key)
        if cache_value == 'test':
            cache.delete(cache_key)
            checks['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            checks['checks']['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache test failed'
            }
            checks['status'] = 'unhealthy'
    except Exception as e:
        logger.error(f'Cache health check failed: {str(e)}')
        checks['checks']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache connection failed: {str(e)}'
        }
        checks['status'] = 'unhealthy'
    
    # 检查静态文件配置
    try:
        static_root = getattr(settings, 'STATIC_ROOT', None)
        checks['checks']['static_files'] = {
            'status': 'healthy' if static_root else 'warning',
            'message': f'STATIC_ROOT: {static_root}' if static_root else 'STATIC_ROOT not configured'
        }
    except Exception as e:
        logger.error(f'Static files check failed: {str(e)}')
        checks['checks']['static_files'] = {
            'status': 'warning',
            'message': f'Static files check error: {str(e)}'
        }
    
    # 根据检查结果设置 HTTP 状态码
    status_code = 200 if checks['status'] == 'healthy' else 503
    
    return JsonResponse(checks, status=status_code)


def readiness_check(request):
    """
    就绪检查端点
    
    用于 Kubernetes/Docker 等容器编排系统的就绪探针
    检查应用是否准备好接收流量
    
    返回：
        JsonResponse: 就绪状态
    """
    try:
        # 检查数据库连接
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'message': 'Application is ready to serve traffic'
        })
    except Exception as e:
        logger.error(f'Readiness check failed: {str(e)}')
        return JsonResponse({
            'status': 'not_ready',
            'message': f'Application is not ready: {str(e)}'
        }, status=503)


def liveness_check(request):
    """
    存活检查端点
    
    用于 Kubernetes/Docker 等容器编排系统的存活探针
    检查应用是否还在运行
    
    返回：
        JsonResponse: 存活状态
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is running'
    })


