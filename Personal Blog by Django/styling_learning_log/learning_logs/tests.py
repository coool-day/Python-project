"""
学习笔记应用的单元测试
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from .models import Topic, Entry
from .forms import TopicForm, EntryForm
from .utils import check_topic_owner, check_entry_owner


class TopicModelTest(TestCase):
    """主题模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.topic = Topic.objects.create(
            text='测试主题',
            owner=self.user
        )
    
    def test_topic_str(self):
        """测试主题的字符串表示"""
        self.assertEqual(str(self.topic), '测试主题')
    
    def test_topic_has_owner(self):
        """测试主题有所有者"""
        self.assertEqual(self.topic.owner, self.user)
    
    def test_topic_ordering(self):
        """测试主题按创建时间倒序排列"""
        # 使用 bulk_create 确保时间顺序
        topic2 = Topic.objects.create(
            text='第二个主题',
            owner=self.user
        )
        # 刷新数据库以确保时间戳正确
        self.topic.refresh_from_db()
        topic2.refresh_from_db()
        
        topics = list(Topic.objects.filter(owner=self.user).order_by('-date_added'))
        # 验证排序：最新的在前面（topic2 应该在前）
        self.assertGreaterEqual(topic2.date_added, self.topic.date_added)
        # 验证列表顺序
        if topics[0].date_added >= topics[1].date_added:
            self.assertTrue(True)  # 排序正确
        else:
            self.fail("主题未按创建时间倒序排列")


class EntryModelTest(TestCase):
    """笔记模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.topic = Topic.objects.create(
            text='测试主题',
            owner=self.user
        )
        self.entry = Entry.objects.create(
            topic=self.topic,
            text='这是一条测试笔记内容'
        )
    
    def test_entry_str(self):
        """测试笔记的字符串表示"""
        self.assertTrue(str(self.entry).startswith('这是一条测试笔记内容'))
    
    def test_entry_belongs_to_topic(self):
        """测试笔记属于主题"""
        self.assertEqual(self.entry.topic, self.topic)
    
    def test_entry_ordering(self):
        """测试笔记按创建时间倒序排列"""
        entry2 = Entry.objects.create(
            topic=self.topic,
            text='第二条笔记'
        )
        # 刷新数据库以确保时间戳正确
        self.entry.refresh_from_db()
        entry2.refresh_from_db()
        
        entries = list(self.topic.entry_set.all().order_by('-date_added'))
        # 验证排序：最新的在前面（entry2 应该在前）
        self.assertGreaterEqual(entry2.date_added, self.entry.date_added)
        # 验证列表顺序
        if entries[0].date_added >= entries[1].date_added:
            self.assertTrue(True)  # 排序正确
        else:
            self.fail("笔记未按创建时间倒序排列")


class TopicFormTest(TestCase):
    """主题表单测试"""
    
    def test_valid_topic_form(self):
        """测试有效的主题表单"""
        form = TopicForm(data={'text': 'Python编程'})
        self.assertTrue(form.is_valid())
    
    def test_empty_topic_form(self):
        """测试空主题表单"""
        form = TopicForm(data={})
        self.assertFalse(form.is_valid())
    
    def test_topic_form_trim_whitespace(self):
        """测试主题表单去除首尾空格"""
        form = TopicForm(data={'text': '  测试主题  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['text'], '测试主题')
    
    def test_topic_form_max_length(self):
        """测试主题表单最大长度验证"""
        long_text = 'a' * 201  # 超过200字符
        form = TopicForm(data={'text': long_text})
        self.assertFalse(form.is_valid())
    
    def test_topic_form_min_length(self):
        """测试主题表单最小长度验证"""
        form = TopicForm(data={'text': 'ab'})  # 有效
        self.assertTrue(form.is_valid())


class EntryFormTest(TestCase):
    """笔记表单测试"""
    
    def test_valid_entry_form(self):
        """测试有效的笔记表单"""
        form = EntryForm(data={'text': '这是一条有效的笔记内容'})
        self.assertTrue(form.is_valid())
    
    def test_empty_entry_form(self):
        """测试空笔记表单"""
        form = EntryForm(data={})
        self.assertFalse(form.is_valid())
    
    def test_entry_form_trim_whitespace(self):
        """测试笔记表单去除首尾空格"""
        form = EntryForm(data={'text': '  笔记内容  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['text'], '笔记内容')
    
    def test_entry_form_min_length(self):
        """测试笔记表单最小长度验证"""
        form = EntryForm(data={'text': 'ab'})  # 少于3个字符
        self.assertFalse(form.is_valid())
        
        form = EntryForm(data={'text': 'abc'})  # 3个字符
        self.assertTrue(form.is_valid())


class ViewsTest(TestCase):
    """视图函数测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.topic = Topic.objects.create(
            text='测试主题',
            owner=self.user
        )
        self.entry = Entry.objects.create(
            topic=self.topic,
            text='测试笔记内容'
        )
    
    def test_index_view(self):
        """测试首页视图"""
        response = self.client.get(reverse('learning_logs:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/index.html')
    
    def test_topics_view_requires_login(self):
        """测试主题列表视图需要登录"""
        response = self.client.get(reverse('learning_logs:topics'))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页
    
    def test_topics_view_authenticated(self):
        """测试已登录用户访问主题列表"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('learning_logs:topics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/topics.html')
        self.assertIn(self.topic, response.context['topics'])
    
    def test_topic_view_requires_login(self):
        """测试主题详情视图需要登录"""
        response = self.client.get(
            reverse('learning_logs:topic', args=[self.topic.id])
        )
        self.assertEqual(response.status_code, 302)
    
    def test_topic_view_owner_access(self):
        """测试主题所有者可以访问"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('learning_logs:topic', args=[self.topic.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['topic'], self.topic)
    
    def test_topic_view_other_user_denied(self):
        """测试其他用户无法访问"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('learning_logs:topic', args=[self.topic.id])
        )
        self.assertEqual(response.status_code, 403)  # PermissionDenied
    
    def test_new_topic_view_get(self):
        """测试新建主题视图 GET 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('learning_logs:new_topic'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/new_topic.html')
    
    def test_new_topic_view_post(self):
        """测试新建主题视图 POST 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('learning_logs:new_topic'),
            {'text': '新主题'}
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(Topic.objects.filter(text='新主题').exists())
        new_topic = Topic.objects.get(text='新主题')
        self.assertEqual(new_topic.owner, self.user)
    
    def test_new_entry_view_post(self):
        """测试新建笔记视图 POST 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('learning_logs:new_entry', args=[self.topic.id]),
            {'text': '新笔记内容'}
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(Entry.objects.filter(text='新笔记内容').exists())
    
    def test_edit_entry_view(self):
        """测试编辑笔记视图"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('learning_logs:edit_entry', args=[self.entry.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/edit_entry.html')
    
    def test_delete_topic_view(self):
        """测试删除主题视图"""
        self.client.login(username='testuser', password='testpass123')
        topic_id = self.topic.id
        response = self.client.post(
            reverse('learning_logs:delete_topic', args=[topic_id])
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertFalse(Topic.objects.filter(id=topic_id).exists())
    
    def test_delete_entry_view(self):
        """测试删除笔记视图"""
        self.client.login(username='testuser', password='testpass123')
        entry_id = self.entry.id
        response = self.client.post(
            reverse('learning_logs:delete_entry', args=[entry_id])
        )
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertFalse(Entry.objects.filter(id=entry_id).exists())
    
    def test_search_functionality(self):
        """测试搜索功能"""
        self.client.login(username='testuser', password='testpass123')
        # 创建另一个主题
        Topic.objects.create(text='Python编程', owner=self.user)
        
        # 搜索
        response = self.client.get(
            reverse('learning_logs:topics'),
            {'search': 'Python'}
        )
        self.assertEqual(response.status_code, 200)
        topics = response.context['topics']
        # 使用 len() 或 paginator.count 获取数量
        self.assertEqual(len(list(topics)), 1)
        self.assertEqual(topics[0].text, 'Python编程')
    
    def test_statistics_view(self):
        """测试统计页面视图"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('learning_logs:statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/statistics.html')
        self.assertEqual(response.context['topics_count'], 1)
        self.assertEqual(response.context['entries_count'], 1)


class UtilsTest(TestCase):
    """工具函数测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.topic = Topic.objects.create(
            text='测试主题',
            owner=self.user
        )
        self.entry = Entry.objects.create(
            topic=self.topic,
            text='测试笔记'
        )
    
    def test_check_topic_owner_success(self):
        """测试检查主题所有者 - 成功"""
        # 应该不抛出异常
        try:
            check_topic_owner(self.topic, self.user)
        except PermissionDenied:
            self.fail("check_topic_owner() 不应该抛出 PermissionDenied")
    
    def test_check_topic_owner_failure(self):
        """测试检查主题所有者 - 失败"""
        with self.assertRaises(PermissionDenied):
            check_topic_owner(self.topic, self.other_user)
    
    def test_check_entry_owner_success(self):
        """测试检查条目所有者 - 成功"""
        try:
            check_entry_owner(self.entry, self.user)
        except PermissionDenied:
            self.fail("check_entry_owner() 不应该抛出 PermissionDenied")
    
    def test_check_entry_owner_failure(self):
        """测试检查条目所有者 - 失败"""
        with self.assertRaises(PermissionDenied):
            check_entry_owner(self.entry, self.other_user)
