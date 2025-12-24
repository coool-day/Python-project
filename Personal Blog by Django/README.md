# 📚 学习笔记 (Learning Log)

一个功能完整、界面美观的 Django 学习笔记管理系统，帮助用户记录和管理学习主题和笔记。

## ✨ 功能特性

### 核心功能
- ✅ **用户系统**：注册、登录、密码修改、用户资料
- ✅ **主题管理**：创建、查看、搜索、删除学习主题
- ✅ **笔记管理**：添加、编辑、删除学习笔记
- ✅ **搜索功能**：支持主题和笔记内容搜索
- ✅ **分页功能**：主题和笔记列表分页显示
- ✅ **数据统计**：学习数据统计和可视化
- ✅ **数据导出**：支持 JSON、CSV、Markdown 格式导出

### 界面特性
- ✅ **中文界面**：完整的中文支持和本地化
- ✅ **响应式设计**：完美适配桌面、平板、手机
- ✅ **美观界面**：现代化的 UI 设计，符合学习笔记风格
- ✅ **交互增强**：丰富的动画效果和用户反馈

### 技术特性
- ✅ **安全性**：权限检查、CSRF 保护、环境变量配置
- ✅ **性能优化**：数据库查询优化、索引优化
- ✅ **代码质量**：完善的异常处理、表单验证
- ✅ **可维护性**：清晰的代码结构、完整的文档

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Django 4.1+
- pip（Python 包管理器）

### 2. 安装依赖

使用 `requirements.txt` 安装所有依赖：

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install django django-bootstrap5
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`：

**Windows:**
```bash
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下变量：

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**⚠️ 生产环境注意事项**：
- 设置一个强密码作为 `SECRET_KEY`（可以使用 `python manage.py shell` 生成）
- 将 `DEBUG` 设置为 `False`
- 在 `ALLOWED_HOSTS` 中添加你的域名（用逗号分隔）

### 4. 运行数据库迁移

```bash
python manage.py migrate
```

### 5. 创建超级用户（可选，用于管理后台）

```bash
python manage.py createsuperuser
```

### 6. 收集静态文件（生产环境）

```bash
python manage.py collectstatic
```

### 7. 运行开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000 查看应用。

## 🧹 代码规范与提交建议

- 安装开发依赖（可选，便于格式化和检查）：
  ```bash
  pip install -r requirements-dev.txt
  ```
- 代码格式化：
  ```bash
  black .
  isort .
  ```
- 代码静态检查：
  ```bash
  flake8
  ```
- 提交前自动检查（推荐）：
  ```bash
  pre-commit install      # 仅需执行一次
  pre-commit run --all-files
  ```
- 配置约定：
  - 统一使用 LF 换行、UTF-8 编码（见 `.editorconfig`）
  - 行宽 100，Black + isort 组合格式化
  - Flake8 忽略项：E203/E266/E501/W503

## 📁 项目结构

```
styling_learning_log/
├── accounts/                    # 用户账户应用
│   ├── forms.py                # 自定义表单（注册、登录、密码修改）
│   ├── views.py                # 视图函数
│   ├── tests.py                # 单元测试
│   └── templates/              # 模板文件
│       └── registration/
│           ├── login.html
│           ├── register.html
│           ├── profile.html
│           └── password_change.html
│
├── learning_logs/              # 学习笔记应用
│   ├── models.py              # 数据模型（Topic、Entry）
│   ├── views.py               # 视图函数（CRUD、搜索、统计、导出）
│   ├── forms.py               # 表单定义
│   ├── admin.py               # 管理后台配置
│   ├── utils.py               # 工具函数
│   ├── tests.py               # 单元测试
│   ├── urls.py                # URL 路由配置
│   └── templates/             # 模板文件
│       └── learning_logs/
│           ├── base.html
│           ├── index.html
│           ├── topics.html
│           ├── topic.html
│           ├── new_topic.html
│           ├── new_entry.html
│           ├── edit_entry.html
│           ├── delete_topic.html
│           ├── delete_entry.html
│           └── statistics.html
│
├── ll_project/                # 项目配置
│   ├── settings.py            # Django 设置（环境变量、国际化、静态文件）
│   ├── urls.py                # 主 URL 配置
│   ├── wsgi.py                # WSGI 配置
│   └── asgi.py                # ASGI 配置
│
├── static/                     # 静态文件目录
│   ├── css/
│   │   └── custom.css         # 自定义样式
│   ├── js/
│   │   └── custom.js          # 自定义 JavaScript
│   └── images/                # 图片文件
│
├── media/                      # 媒体文件目录（用户上传）
├── staticfiles/               # 生产环境静态文件（运行 collectstatic 后生成）
│
├── .env                       # 环境变量（不提交到版本控制）
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略文件
├── requirements.txt           # Python 依赖列表
├── manage.py                  # Django 管理脚本
│
└── 文档文件/
    ├── README.md              # 项目说明文档
    ├── PROJECT_IMPROVEMENTS.md  # 项目完善计划
    ├── CODE_QUALITY_IMPROVEMENTS.md  # 代码质量改进报告
    ├── FEATURE_EXTENSION_SUMMARY.md  # 功能扩展总结
    ├── I18N_LOCALIZATION_SUMMARY.md  # 国际化总结
    └── STATIC_FILES_SUMMARY.md  # 静态文件总结
```

## 🧪 运行测试

项目包含完整的单元测试，运行测试：

```bash
python manage.py test
```

运行特定应用的测试：

```bash
python manage.py test learning_logs
python manage.py test accounts
```

查看测试覆盖率（需要安装 coverage）：

```bash
coverage run --source='.' manage.py test
coverage report
```

## 📖 使用指南

### 基本使用流程

1. **注册账户**
   - 访问首页，点击"注册"
   - 填写用户名和密码
   - 注册成功后自动登录

2. **创建主题**
   - 登录后点击"我的主题"
   - 点击"添加新主题"
   - 输入主题名称并保存

3. **添加笔记**
   - 在主题详情页面点击"添加新笔记"
   - 输入笔记内容并保存

4. **搜索和筛选**
   - 在主题列表或笔记列表页面使用搜索框
   - 输入关键词进行搜索

5. **查看统计**
   - 点击导航栏的"统计"按钮
   - 查看学习数据统计

6. **导出数据**
   - 在统计页面点击导出按钮
   - 选择导出格式（JSON、CSV、Markdown）

### 管理后台

访问 http://127.0.0.1:8000/admin/ 使用管理后台（需要超级用户权限）。

## 🔒 安全说明

### 开发环境
- `.env` 文件包含敏感信息，已添加到 `.gitignore`
- 默认 `DEBUG=True`，仅用于开发

### 生产环境部署前检查清单

- [ ] 设置强密码 `SECRET_KEY`
- [ ] 设置 `DEBUG=False`
- [ ] 配置 `ALLOWED_HOSTS`（添加实际域名）
- [ ] 配置 HTTPS（SSL 证书）
- [ ] 运行 `collectstatic` 收集静态文件
- [ ] 配置 Web 服务器（Nginx/Apache）提供静态文件
- [ ] 设置数据库备份策略
- [ ] 配置日志系统
- [ ] 设置文件上传限制

## 🛠️ 开发指南

### 添加新功能

1. **添加新模型**：
   - 在 `models.py` 中定义模型
   - 运行 `python manage.py makemigrations`
   - 运行 `python manage.py migrate`

2. **添加新视图**：
   - 在 `views.py` 中编写视图函数
   - 在 `urls.py` 中添加 URL 路由
   - 创建对应的模板文件

3. **添加新表单**：
   - 在 `forms.py` 中定义表单类
   - 在视图中使用表单

### 代码规范

- 使用中文注释和文档字符串
- 遵循 PEP 8 代码风格
- 编写单元测试
- 使用有意义的变量和函数名

## 📚 相关文档

- [项目完善计划](PROJECT_IMPROVEMENTS.md) - 了解项目改进计划
- [代码质量改进](CODE_QUALITY_IMPROVEMENTS.md) - 代码质量提升详情
- [功能扩展总结](FEATURE_EXTENSION_SUMMARY.md) - 功能扩展详情
- [国际化总结](I18N_LOCALIZATION_SUMMARY.md) - 国际化配置详情
- [静态文件总结](STATIC_FILES_SUMMARY.md) - 静态文件配置详情

## 🐛 常见问题

### 1. SSL 协议错误

如果浏览器显示 SSL 错误，请：
- 确保使用 `http://` 而不是 `https://`
- 清除浏览器 HSTS 缓存
- 使用 `localhost` 而不是 `127.0.0.1`

详细解决方案见 [SSL_FIX_GUIDE.md](SSL_FIX_GUIDE.md)

### 2. 静态文件不显示

- 确保运行了 `python manage.py collectstatic`（生产环境）
- 检查 `STATIC_URL` 和 `STATIC_ROOT` 配置
- 检查 Web 服务器配置

### 3. 数据库迁移错误

- 检查数据库连接
- 确保所有迁移文件存在
- 尝试 `python manage.py migrate --run-syncdb`

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习使用。

## 🙏 致谢

- Django 框架
- Bootstrap 5
- django-bootstrap5

---

**最后更新**：2024年12月

