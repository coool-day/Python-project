from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Topic, Entry


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """主题管理后台配置"""
    list_display = ['text', 'owner', 'entry_count', 'date_added', 'formatted_date_added']
    list_filter = ['date_added', 'owner']
    search_fields = ['text', 'owner__username']
    readonly_fields = ['date_added', 'formatted_date_added']
    list_per_page = 20
    date_hierarchy = 'date_added'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('text', 'owner')
        }),
        ('时间信息', {
            'fields': ('date_added', 'formatted_date_added'),
            'classes': ('collapse',)
        }),
    )
    
    def entry_count(self, obj):
        """显示该主题下的笔记数量"""
        count = obj.entry_set.count()
        if count > 0:
            return format_html(
                '<span style="color: #4a90e2; font-weight: bold;">{}</span>',
                f'{count} 条笔记'
            )
        return '0 条笔记'
    entry_count.short_description = '笔记数量'
    entry_count.admin_order_field = 'entry_set__count'
    
    def formatted_date_added(self, obj):
        """格式化显示创建时间"""
        if obj.date_added:
            # 转换为本地时区
            local_time = timezone.localtime(obj.date_added)
            return local_time.strftime('%Y年%m月%d日 %H:%M:%S')
        return '-'
    formatted_date_added.short_description = '创建时间（格式化）'
    
    def get_queryset(self, request):
        """优化查询性能"""
        qs = super().get_queryset(request)
        return qs.select_related('owner').prefetch_related('entry_set')


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    """笔记管理后台配置"""
    list_display = ['topic', 'text_preview', 'owner', 'formatted_date_added']
    list_filter = ['date_added', 'topic', 'topic__owner']
    search_fields = ['text', 'topic__text', 'topic__owner__username']
    readonly_fields = ['date_added', 'formatted_date_added']
    list_per_page = 20
    date_hierarchy = 'date_added'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('topic', 'text')
        }),
        ('时间信息', {
            'fields': ('date_added', 'formatted_date_added'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """显示笔记内容预览"""
        preview = obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
        return format_html(
            '<span style="color: #555;">{}</span>',
            preview
        )
    text_preview.short_description = '笔记内容'
    text_preview.admin_order_field = 'text'
    
    def owner(self, obj):
        """显示笔记所属主题的所有者"""
        return obj.topic.owner.username
    owner.short_description = '所有者'
    owner.admin_order_field = 'topic__owner__username'
    
    def formatted_date_added(self, obj):
        """格式化显示创建时间"""
        if obj.date_added:
            # 转换为本地时区
            local_time = timezone.localtime(obj.date_added)
            return local_time.strftime('%Y年%m月%d日 %H:%M:%S')
        return '-'
    formatted_date_added.short_description = '创建时间（格式化）'
    
    def get_queryset(self, request):
        """优化查询性能"""
        qs = super().get_queryset(request)
        return qs.select_related('topic', 'topic__owner')