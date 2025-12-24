from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import Http404, JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.cache import cache
import json
import csv
from datetime import datetime

from .models import Topic, Entry
from .forms import TopicForm, EntryForm
from .utils import check_topic_owner, check_entry_owner


def index(request):
    """
    学习笔记首页视图
    
    显示欢迎页面，引导用户注册或登录。
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 渲染的首页模板
    """
    return render(request, 'learning_logs/index.html')


@login_required
def topics(request):
    """
    显示所有主题列表视图（支持搜索和分页）
    
    功能：
    - 显示当前用户的所有主题
    - 支持关键词搜索（不区分大小写）
    - 分页显示（每页10个主题）
    - 按创建时间倒序排列
    
    Args:
        request: HTTP 请求对象
            - GET 参数：
                - search: 搜索关键词（可选）
                - page: 页码（可选）
        
    Returns:
        HttpResponse: 渲染的主题列表模板
    """
    try:
        # 获取搜索关键词
        search_query = request.GET.get('search', '')
        # 使用 select_related 优化查询（虽然这里没有外键，但保持一致性）
        topics_list = Topic.objects.filter(owner=request.user).select_related('owner')

        # 搜索功能
        if search_query:
            topics_list = topics_list.filter(text__icontains=search_query)

        # 排序（使用索引字段）
        topics_list = topics_list.order_by('-date_added')

        # 分页
        paginator = Paginator(topics_list, 10)  # 每页10个主题
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # 使用 paginator.count 而不是重新查询
        context = {
            'topics': page_obj,
            'search_query': search_query,
            'total_count': paginator.count,
        }
        return render(request, 'learning_logs/topics.html', context)
    except Exception as e:
        messages.error(request, f'❌ 加载主题列表时出错：{str(e)}')
        return render(request, 'learning_logs/topics.html', {'topics': []})

@login_required
def topic(request, topic_id):
    """
    显示单个主题详情视图（支持搜索和分页）
    
    功能：
    - 显示主题的详细信息
    - 显示该主题下的所有笔记
    - 支持笔记内容搜索
    - 分页显示（每页5条笔记）
    - 权限检查：确保用户只能访问自己的主题
    
    Args:
        request: HTTP 请求对象
        topic_id: 主题ID
            - GET 参数：
                - search: 搜索关键词（可选）
                - page: 页码（可选）
        
    Returns:
        HttpResponse: 渲染的主题详情模板
        
    Raises:
        Http404: 主题不存在
        PermissionDenied: 用户无权访问此主题
    """
    topic_obj = get_object_or_404(Topic, id=topic_id)
    # 确保主题属于当前用户
    check_topic_owner(topic_obj, request.user)

    # 获取搜索关键词
    search_query = request.GET.get('search', '')
    entries = topic_obj.entry_set.select_related('topic').order_by('-date_added')
    
    # 搜索功能
    if search_query:
        entries = entries.filter(text__icontains=search_query)
    
    # 分页
    paginator = Paginator(entries, 5)  # 每页5条笔记
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'topic': topic_obj,
        'entries': page_obj,
        'search_query': search_query,
        'total_count': entries.count(),
    }
    return render(request, 'learning_logs/topic.html', context)

@login_required    
def new_topic(request):
    """
    创建新主题视图
    
    功能：
    - GET: 显示创建主题表单
    - POST: 处理表单提交，创建新主题
    - 自动设置主题所有者为当前用户
    - 表单验证和错误处理
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 
            - GET: 渲染创建主题表单
            - POST: 成功则重定向到主题列表，失败则显示表单和错误
    """
    if request.method != 'POST':
        # 未提交数据；创建空白表单
        form = TopicForm()
    else:
        # POST 数据已提交；处理数据
        form = TopicForm(data=request.POST)
        if form.is_valid():
            try:
                new_topic_obj = form.save(commit=False)
                new_topic_obj.owner = request.user
                new_topic_obj.save()
                messages.success(request, f'✅ 主题 "{new_topic_obj.text}" 已成功创建！')
                return redirect('learning_logs:topics')
            except IntegrityError:
                messages.error(request, '❌ 创建主题时发生错误，请重试。')
            except Exception as e:
                messages.error(request, f'❌ 创建主题时出错：{str(e)}')
        else:
            # 表单验证失败，显示具体错误
            error_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_list.append(f"{form.fields[field].label}: {error}")
            if error_list:
                messages.error(request, '❌ ' + ' | '.join(error_list))
            else:
                messages.error(request, '❌ 请检查表单中的错误并修正后重试。')

    # 显示空白或无效的表单
    context = {'form': form}
    return render(request, 'learning_logs/new_topic.html', context)

@login_required    
def new_entry(request, topic_id):
    """
    为特定主题添加新笔记视图
    
    功能：
    - GET: 显示创建笔记表单
    - POST: 处理表单提交，创建新笔记
    - 权限检查：确保用户只能为自己的主题添加笔记
    - 表单验证和错误处理
    
    Args:
        request: HTTP 请求对象
        topic_id: 主题ID
        
    Returns:
        HttpResponse:
            - GET: 渲染创建笔记表单
            - POST: 成功则重定向到主题详情，失败则显示表单和错误
            
    Raises:
        Http404: 主题不存在
        PermissionDenied: 用户无权为此主题添加笔记
    """
    topic_obj = get_object_or_404(Topic, id=topic_id)
    # 确保主题属于当前用户
    check_topic_owner(topic_obj, request.user)
    
    if request.method != 'POST':
        # 未提交数据；创建空白表单
        form = EntryForm()
    else:
        # POST 数据已提交；处理数据
        form = EntryForm(data=request.POST)
        if form.is_valid():
            try:
                new_entry_obj = form.save(commit=False)
                new_entry_obj.topic = topic_obj
                new_entry_obj.save()
                messages.success(request, '✅ 笔记已成功添加！')
                return redirect('learning_logs:topic', topic_id=topic_id)
            except IntegrityError:
                messages.error(request, '❌ 添加笔记时发生错误，请重试。')
            except Exception as e:
                messages.error(request, f'❌ 添加笔记时出错：{str(e)}')
        else:
            # 表单验证失败，显示具体错误
            error_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_list.append(f"{form.fields[field].label}: {error}")
            if error_list:
                messages.error(request, '❌ ' + ' | '.join(error_list))
            else:
                messages.error(request, '❌ 请检查表单中的错误并修正后重试。')

    # 显示空白或无效的表单
    context = {'topic': topic_obj, 'form': form}
    return render(request, 'learning_logs/new_entry.html', context)

@login_required
def edit_entry(request, entry_id):
    """
    编辑现有笔记视图
    
    功能：
    - GET: 显示编辑表单（预填充当前笔记内容）
    - POST: 处理表单提交，更新笔记
    - 权限检查：确保用户只能编辑自己主题下的笔记
    - 表单验证和错误处理
    
    Args:
        request: HTTP 请求对象
        entry_id: 笔记ID
        
    Returns:
        HttpResponse:
            - GET: 渲染编辑表单
            - POST: 成功则重定向到主题详情，失败则显示表单和错误
            
    Raises:
        Http404: 笔记不存在
        PermissionDenied: 用户无权编辑此笔记
    """
    entry = get_object_or_404(Entry.objects.select_related('topic'), id=entry_id)
    topic_obj = entry.topic
    # 确保条目所属的主题属于当前用户
    check_entry_owner(entry, request.user)

    if request.method != 'POST':
        # 初始请求；使用当前条目预填充表单
        form = EntryForm(instance=entry)
    else:
        # POST 数据已提交；处理数据
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '✅ 笔记已成功更新！')
                return redirect('learning_logs:topic', topic_id=topic_obj.id)
            except IntegrityError:
                messages.error(request, '❌ 更新笔记时发生错误，请重试。')
            except Exception as e:
                messages.error(request, f'❌ 更新笔记时出错：{str(e)}')
        else:
            # 表单验证失败，显示具体错误
            error_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_list.append(f"{form.fields[field].label}: {error}")
            if error_list:
                messages.error(request, '❌ ' + ' | '.join(error_list))
            else:
                messages.error(request, '❌ 请检查表单中的错误并修正后重试。')

    context = {'entry': entry, 'topic': topic_obj, 'form': form}
    return render(request, 'learning_logs/edit_entry.html', context)


@login_required
def delete_topic(request, topic_id):
    """
    删除主题视图
    
    功能：
    - GET: 显示删除确认页面
    - POST: 执行删除操作（级联删除所有笔记）
    - 权限检查：确保用户只能删除自己的主题
    - 显示成功/失败消息
    
    Args:
        request: HTTP 请求对象
        topic_id: 主题ID
        
    Returns:
        HttpResponse:
            - GET: 渲染删除确认页面
            - POST: 重定向到主题列表
            
    Raises:
        Http404: 主题不存在
        PermissionDenied: 用户无权删除此主题
    """
    topic_obj = get_object_or_404(Topic, id=topic_id)
    # 确保主题属于当前用户
    check_topic_owner(topic_obj, request.user)
    
    if request.method == 'POST':
        try:
            topic_text = topic_obj.text
            topic_obj.delete()
            
            # 清除用户统计缓存
            cache_key = f'user_stats_{request.user.id}'
            cache.delete(cache_key)
            
            messages.success(request, f'✅ 主题 "{topic_text}" 已成功删除！')
            return redirect('learning_logs:topics')
        except Exception as e:
            messages.error(request, f'❌ 删除主题时出错：{str(e)}')
            return redirect('learning_logs:topics')
    
    # GET 请求显示确认页面
    context = {'topic': topic_obj}
    return render(request, 'learning_logs/delete_topic.html', context)


@login_required
def delete_entry(request, entry_id):
    """
    删除笔记视图
    
    功能：
    - GET: 显示删除确认页面
    - POST: 执行删除操作
    - 权限检查：确保用户只能删除自己主题下的笔记
    - 显示成功/失败消息
    
    Args:
        request: HTTP 请求对象
        entry_id: 笔记ID
        
    Returns:
        HttpResponse:
            - GET: 渲染删除确认页面
            - POST: 重定向到主题详情
            
    Raises:
        Http404: 笔记不存在
        PermissionDenied: 用户无权删除此笔记
    """
    entry = get_object_or_404(Entry.objects.select_related('topic'), id=entry_id)
    topic_obj = entry.topic
    # 确保条目所属的主题属于当前用户
    check_entry_owner(entry, request.user)
    
    if request.method == 'POST':
        try:
            topic_id = topic_obj.id
            entry.delete()
            messages.success(request, '✅ 笔记已成功删除！')
            return redirect('learning_logs:topic', topic_id=topic_id)
        except Exception as e:
            messages.error(request, f'❌ 删除笔记时出错：{str(e)}')
            return redirect('learning_logs:topic', topic_id=topic_obj.id)
    
    # GET 请求显示确认页面
    context = {'entry': entry, 'topic': topic_obj}
    return render(request, 'learning_logs/delete_entry.html', context)


@login_required
def statistics(request):
    """
    数据统计页面视图
    
    功能：
    - 显示用户的学习统计数据
    - 主题总数和笔记总数
    - 最近创建的主题（前5个）
    - 最近添加的笔记（前10条）
    - 主题笔记数量排行（前10个）
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 渲染的统计页面模板
    """
    from django.core.cache import cache
    from django.conf import settings
    
    # 使用缓存键
    cache_key = f'user_stats_{request.user.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data and not settings.DEBUG:  # 开发环境不使用缓存以便调试
        return render(request, 'learning_logs/statistics.html', cached_data)
    
    try:
        # 使用单个查询获取统计信息（优化：减少查询次数）
        topics_count = Topic.objects.filter(owner=request.user).count()
        entries_count = Entry.objects.filter(topic__owner=request.user).count()
        
        # 获取最近的主题（使用 select_related 优化）
        recent_topics = Topic.objects.filter(owner=request.user).select_related('owner').order_by('-date_added')[:5]
        
        # 获取最近的活动（最近添加的笔记）
        # 使用 select_related 优化，避免 N+1 查询
        recent_entries = Entry.objects.filter(
            topic__owner=request.user
        ).select_related('topic', 'topic__owner').order_by('-date_added')[:10]
        
        # 按主题统计笔记数量
        # 使用 annotate 和 Count 在数据库层面统计，避免 Python 层面的循环
        topic_stats = Topic.objects.filter(owner=request.user).select_related('owner').annotate(
            entry_count=Count('entry')
        ).order_by('-entry_count')[:10]
        
        context = {
            'topics_count': topics_count,
            'entries_count': entries_count,
            'recent_topics': recent_topics,
            'recent_entries': recent_entries,
            'topic_stats': topic_stats,
        }
        
        # 缓存结果（5分钟）
        if not settings.DEBUG:
            cache.set(cache_key, context, 300)
        
        return render(request, 'learning_logs/statistics.html', context)
    except Exception as e:
        messages.error(request, f'❌ 加载统计数据时出错：{str(e)}')
        return redirect('learning_logs:topics')


@login_required
def export_data(request, format_type='json'):
    """
    数据导出视图
    
    功能：
    - 导出用户的所有学习数据
    - 支持多种格式：JSON、CSV、Markdown
    - 自动生成带日期的文件名
    - 包含用户名和导出时间
    
    Args:
        request: HTTP 请求对象
        format_type: 导出格式（'json'、'csv'、'markdown'）
        
    Returns:
        HttpResponse: 
            - 文件下载响应（JSON/CSV/Markdown）
            - 或重定向到主题列表（格式不支持时）
            
    Raises:
        Exception: 导出过程中发生错误
    """
    try:
        topics_list = Topic.objects.filter(owner=request.user).prefetch_related('entry_set')
        
        if format_type == 'json':
            data = {
                'user': request.user.username,
                'export_date': datetime.now().isoformat(),
                'topics': []
            }
            for topic in topics_list:
                topic_data = {
                    'text': topic.text,
                    'date_added': topic.date_added.isoformat(),
                    'entries': []
                }
                for entry in topic.entry_set.all():
                    topic_data['entries'].append({
                        'text': entry.text,
                        'date_added': entry.date_added.isoformat(),
                    })
                data['topics'].append(topic_data)
            
            response = HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="learning_log_{datetime.now().strftime("%Y%m%d")}.json"'
            return response
        
        elif format_type == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="learning_log_{datetime.now().strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['主题', '笔记内容', '笔记日期'])
            
            for topic in topics_list:
                for entry in topic.entry_set.all():
                    writer.writerow([
                        topic.text,
                        entry.text,
                        entry.date_added.strftime('%Y-%m-%d %H:%M:%S')
                    ])
            return response
        
        elif format_type == 'markdown':
            content = f"# 学习笔记导出\n\n"
            content += f"**导出时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
            content += f"**用户**: {request.user.username}\n\n"
            content += "---\n\n"
            
            for topic in topics_list:
                content += f"## {topic.text}\n\n"
                content += f"*创建时间: {topic.date_added.strftime('%Y年%m月%d日 %H:%M:%S')}*\n\n"
                
                for entry in topic.entry_set.all():
                    content += f"### {entry.date_added.strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
                    content += f"{entry.text}\n\n"
                    content += "---\n\n"
            
            response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="learning_log_{datetime.now().strftime("%Y%m%d")}.md"'
            return response
        
        else:
            messages.error(request, '❌ 不支持的导出格式。')
            return redirect('learning_logs:topics')
            
    except Exception as e:
        messages.error(request, f'❌ 导出数据时出错：{str(e)}')
        return redirect('learning_logs:topics')