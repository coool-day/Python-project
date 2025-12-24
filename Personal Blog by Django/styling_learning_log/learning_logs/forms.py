from django import forms

from .models import Topic, Entry


class TopicForm(forms.ModelForm):
    """主题表单"""
    
    class Meta:
        model = Topic
        fields = ['text', 'color', 'icon', 'cover_image_url']
        labels = {
            'text': '主题名称',
            'color': '主题颜色',
            'icon': '主题图标',
            'cover_image_url': '主题封面图片链接',
        }
        help_texts = {
            'text': '请输入学习主题的名称（最多200个字符）',
            'color': '选择主题的显示颜色',
            'icon': '为主题选择一个图标（emoji，例如：📚、💻、🎨）',
            'cover_image_url': '可选，粘贴一张图片的网络地址作为封面（建议 16:9 或 4:3 比例）',
        }
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：Python编程、机器学习、Web开发...',
                'maxlength': '200',
                'autofocus': True,
            }),
            'color': forms.Select(attrs={
                'class': 'form-select',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📚',
                'maxlength': '50',
            }),
            'cover_image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：https://images.unsplash.com/...',
                'maxlength': '300',
            }),
        }
        error_messages = {
            'text': {
                'required': '请输入主题名称。',
                'max_length': '主题名称不能超过200个字符。',
            }
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保字段有正确的类名
        self.fields['text'].widget.attrs.update({
            'class': 'form-control',
        })
    
    def clean_text(self):
        """清理和验证主题文本"""
        text = self.cleaned_data.get('text')
        if text:
            # 去除首尾空格
            text = text.strip()
            # 检查是否为空（去除空格后）
            if not text:
                raise forms.ValidationError('主题名称不能为空。')
            # 检查长度
            if len(text) > 200:
                raise forms.ValidationError('主题名称不能超过200个字符。')
            # 检查是否包含特殊字符（可选，根据需求调整）
            if text.startswith(' ') or text.endswith(' '):
                text = text.strip()
        return text


class EntryForm(forms.ModelForm):
    """笔记表单"""
    
    class Meta:
        model = Entry
        fields = ['text', 'tags', 'is_markdown', 'is_public']
        labels = {
            'text': '笔记内容',
            'tags': '标签',
            'is_markdown': '使用 Markdown 格式',
            'is_public': '公开/私密',
        }
        help_texts = {
            'text': '记录你在这个主题上学到的知识（支持 Markdown 格式）',
            'tags': '用逗号分隔的标签（例如：重要,总结,问题）',
            'is_markdown': '勾选后可以使用 Markdown 语法格式化文本',
            'is_public': '选择"公开"后，此笔记将发布到博客论坛，所有人可以查看和评论；选择"私密"则仅自己可见',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '在这里记录你的学习心得、知识点、总结等...\n\n支持 Markdown 格式：\n- **粗体**\n- *斜体*\n- `代码`\n- # 标题',
                'rows': 12,
                'cols': 80,
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：重要,总结,问题',
            }),
            'is_markdown': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        error_messages = {
            'text': {
                'required': '请输入笔记内容。',
            }
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保字段有正确的类名和样式
        self.fields['text'].widget.attrs.update({
            'class': 'form-control',
            'style': 'min-height: 200px;',
        })
    
    def clean_text(self):
        """清理和验证笔记文本"""
        text = self.cleaned_data.get('text')
        if text:
            # 去除首尾空格
            text = text.strip()
            # 检查是否为空（去除空格后）
            if not text:
                raise forms.ValidationError('笔记内容不能为空。')
            # 检查最小长度（可选，根据需求调整）
            if len(text) < 3:
                raise forms.ValidationError('笔记内容至少需要3个字符。')
        return text


class SearchForm(forms.Form):
    """搜索表单"""
    search = forms.CharField(
        label='搜索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '输入关键词搜索...',
            'autofocus': True,
        })
    )