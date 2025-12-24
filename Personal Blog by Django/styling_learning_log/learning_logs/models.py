from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation


class Topic(models.Model):
    """用户正在学习的主题"""
    # 主题颜色选项
    COLOR_CHOICES = [
        ('primary', '蓝色'),
        ('success', '绿色'),
        ('warning', '黄色'),
        ('danger', '红色'),
        ('info', '青色'),
        ('secondary', '灰色'),
        ('dark', '深色'),
    ]
    
    text = models.CharField(
        max_length=200,
        verbose_name='主题名称',
        help_text='请输入学习主题的名称（最多200个字符）'
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='主题创建的时间'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='所有者',
        help_text='拥有此主题的用户'
    )
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='primary',
        verbose_name='主题颜色',
        help_text='选择主题的显示颜色'
    )
    icon = models.CharField(
        max_length=50,
        default='📌',
        verbose_name='主题图标',
        help_text='为主题选择一个图标（emoji）'
    )
    cover_image_url = models.URLField(
        max_length=300,
        blank=True,
        verbose_name='主题封面图片链接',
        help_text='可选，粘贴一张图片的网络地址作为封面（例如来自图床或 Unsplash）'
    )

    class Meta:
        verbose_name = '主题'
        verbose_name_plural = '主题'
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['owner', '-date_added'], name='topic_owner_date_idx'),
            models.Index(fields=['text'], name='topic_text_idx'),
        ]

    def __str__(self):
        """返回模型的字符串表示"""
        return self.text


class Entry(models.Model):
    """关于某个主题的具体学习内容"""
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='所属主题',
        help_text='此笔记所属的学习主题'
    )
    text = models.TextField(
        verbose_name='笔记内容',
        help_text='记录你在这个主题上学到的知识（支持 Markdown 格式）'
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='笔记创建的时间'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='标签',
        help_text='用逗号分隔的标签（例如：重要,总结,问题）'
    )
    is_markdown = models.BooleanField(
        default=True,
        verbose_name='使用 Markdown',
        help_text='是否使用 Markdown 格式渲染'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='公开/私密',
        help_text='选择"公开"后，此笔记将发布到博客论坛，所有人可以查看和评论；选择"私密"则仅自己可见'
    )
    
    # 关联评论（通过 GenericRelation）
    comments = GenericRelation(
        'blogs.Comment',
        related_query_name='entry',
        verbose_name='评论',
    )

    class Meta:
        verbose_name = '笔记'
        verbose_name_plural = '笔记'
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['topic', '-date_added'], name='entry_topic_date_idx'),
        ]

    def __str__(self):
        """返回条目的简单字符串表示"""
        return f"{self.text[:50]}..."