## 📦 九、部署准备（Deployment）

本项目目前主要在本地开发环境运行。为了将它安全、稳定地部署到生产环境（例如云服务器、学校实验室服务器或公司内网），建议按以下步骤准备。

---

### 1. 配置生产环境 Settings（`settings_production.py`）

**目标：** 区分开发 / 生产配置，生产环境使用更严格的安全设置。

- **已完成（代码中已实现）：**
  - 新增 `ll_project/settings_production.py`，继承基础 `settings.py`，并开启：
    - `DEBUG = False`
    - 严格的安全设置：`SECURE_SSL_REDIRECT`、`SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`、HSTS 等。
  - 为生产环境预留：
    - Redis 缓存（`django-redis`）
    - 日志配置（写入 `logs/django.log`、`logs/django_error.log`）
    - 邮件告警（`EMAIL_*`、`ADMINS`）

- **你需要做的：**
  1. 在服务器上安装依赖：

     ```bash
     pip install -r requirements.txt
     ```

  2. 在生产环境设置环境变量（示例，以 Linux Bash 为例）：

     ```bash
     export DJANGO_SETTINGS_MODULE=ll_project.settings_production
     export SECRET_KEY='生产环境的随机长密钥'
     export ALLOWED_HOSTS='yourdomain.com,127.0.0.1'
     export REDIS_URL='redis://127.0.0.1:6379/1'
     export EMAIL_HOST='smtp.example.com'
     export EMAIL_PORT='587'
     export EMAIL_HOST_USER='your_email@example.com'
     export EMAIL_HOST_PASSWORD='your_password'
     export ADMIN_NAME='Admin'
     export ADMIN_EMAIL='admin@example.com'
     ```

  3. 确保 `.env` 文件 **不提交到 Git**，仅用于本地或服务器私密配置。

---

### 2. 日志系统配置（Logging）

**目标：** 在开发和生产环境中都能记录有用的运行日志，便于排查问题。

- **开发环境（`settings.py` 中已配置）：**
  - 当 `DEBUG=True` 时：
    - 将 Django 和 `learning_logs` 的日志输出到控制台和 `logs/django_dev.log`。
    - 自动创建 `logs/` 目录。

- **生产环境（`settings_production.py` 中已配置）：**
  - 使用 `RotatingFileHandler`：
    - `logs/django.log`：记录一般信息和重要操作。
    - `logs/django_error.log`：记录错误、异常信息。
  - 当发生严重错误时，可通过 `AdminEmailHandler` 给 `ADMINS` 发送邮件。

- **你可以检查的内容：**
  - 部署后，访问几次站点，然后查看日志文件是否生成：

    ```bash
    ls logs
    tail -n 50 logs/django.log
    tail -n 50 logs/django_error.log
    ```

---

### 3. 健康检查与监控（Health Check & Monitoring）

**目标：** 部署后能快速判断服务是否“活着”和“可用”，方便后续接入 Nginx、Kubernetes 或监控系统。

- **已在代码中实现：**
  - 在 `learning_logs/health.py` 中增加了以下端点：
    - `GET /health/`：简单健康检查，返回服务名和版本。
    - `GET /health/detailed/`：详细检查数据库、缓存、静态文件配置等。
    - `GET /health/ready/`：就绪检查（是否可以接收流量）。
    - `GET /health/live/`：存活检查（应用进程是否正常运行）。
  - 在 `learning_logs/urls.py` 中已注册上述路由。

- **你可以在本地验证：**

  ```bash
  # 先启动开发服务器
  python manage.py runserver
  ```

  然后在浏览器中访问：

  - `http://127.0.0.1:8000/health/`
  - `http://127.0.0.1:8000/health/detailed/`
  - `http://127.0.0.1:8000/health/ready/`
  - `http://127.0.0.1:8000/health/live/`

- **后续扩展建议（可选）：**
  - 接入外部监控 / 告警平台，如 Sentry、Prometheus + Grafana 等。
  - 为关键视图增加计时和统计（例如记录响应时间、请求量）。

---

### 4. 静态文件与媒体文件（生产环境）

**目标：** 让 CSS / JS / 图片 等静态资源在生产环境中高效、稳定地提供。

- **当前配置：**
  - 开发环境（`settings.py`）：
    - 使用 `STATIC_URL`、`STATICFILES_DIRS` 提供静态文件。
    - 使用 `MEDIA_URL`、`MEDIA_ROOT` 存储上传文件。
  - 生产环境（`settings_production.py`）：
    - `STATIC_ROOT = BASE_DIR / 'staticfiles'`
    - `MEDIA_ROOT = BASE_DIR / 'media'`

- **部署时需要执行：**

  ```bash
  # 使用生产配置收集静态文件
  export DJANGO_SETTINGS_MODULE=ll_project.settings_production
  python manage.py collectstatic
  ```

  然后在 Nginx 或其他 Web 服务器中，将 `staticfiles/` 和 `media/` 配置为静态资源目录。

- **可选：使用 WhiteNoise 简化部署：**
  - 安装：`pip install whitenoise`
  - 在 `settings_production.py` 中启用（示例已写在注释中）：
    - 在 `MIDDLEWARE` 中插入 `whitenoise.middleware.WhiteNoiseMiddleware`
    - 设置 `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`

---

### 5. 运行方式示例（Gunicorn + Nginx，Linux 环境示意）

**目标：** 提供一个常见的部署参考流程，便于将来迁移到云服务器。

1. **安装 Gunicorn：**

   ```bash
   pip install gunicorn
   ```

2. **使用生产配置启动：**

   ```bash
   export DJANGO_SETTINGS_MODULE=ll_project.settings_production
   gunicorn ll_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```

3. **使用 Nginx 反向代理（伪代码示例）：**

   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location /static/ {
           alias /path/to/project/staticfiles/;
       }

       location /media/ {
           alias /path/to/project/media/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

> 说明：你目前在 Windows 本机开发，上述示例更适合未来迁移到 Linux 服务器时参考使用。

---

### 6. 错误日志与告警

**目标：** 一旦线上出现 500 错误或异常，能够尽快发现并排查。

- **错误日志：**
  - 生产环境下，所有错误会写入 `logs/django_error.log`。
  - 建议定期查看该文件，或者用脚本监控其中的“ERROR”级别信息。

- **邮件告警（可选）：**
  - 在生产环境中设置 `EMAIL_*` 和 `ADMINS` 后：
    - 当 `DEBUG=False` 且发生未处理的 500 错误时，Django 会自动给 `ADMINS` 发送错误邮件。
  - 建议使用专用的发件邮箱，例如：
    - `learning-log-bot@example.com`

---

### 7. 数据库备份策略（建议）

**目标：** 防止误删数据或磁盘损坏导致的学习笔记丢失。

- **本地 SQLite 阶段：**
  - 目前项目默认使用 SQLite 数据库（一个 `.sqlite3` 文件）。
  - 建议：
    - 定期复制数据库文件备份，例如：

      ```bash
      cp db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3
      ```

    - 将 `backups/` 目录同步到网盘 / U 盘 / 云盘等安全位置。

- **迁移到 PostgreSQL / MySQL 之后：**
  - 建议使用数据库自带的备份工具：
    - PostgreSQL：`pg_dump` + 定时任务（crontab）
    - MySQL：`mysqldump` + 定时任务
  - 可以将备份脚本记录在单独的 `backup_scripts/` 目录，并在此文档中说明使用方法。

---

### 8. 部署前检查清单（Checklist）

在真正对外开放之前，建议按下面的清单逐项确认：

- [ ] 使用 `settings_production.py` 并确认 `DEBUG=False`
- [ ] 配置 `ALLOWED_HOSTS`，仅包含你的域名 / IP
- [ ] 已设置强随机的 `SECRET_KEY`，且 **不写死在代码里**
- [ ] 数据库账号、密码使用环境变量配置
- [ ] 已执行 `python manage.py collectstatic`
- [ ] 静态文件和媒体文件路径在 Web 服务器中配置正确
- [ ] 日志文件（`logs/`）已生成，并验证能记录正常访问和错误
- [ ] `/health/`、`/health/detailed/` 等健康检查端点返回正常
- [ ] 至少做一次数据库备份，并验证备份文件可用
- [ ] 自测主要功能（注册 / 登录 / 新建主题 / 新建笔记 / 搜索 / 导出）均可正常使用

---

### 9. 后续可以进一步完善的方向

- 使用 Docker 打包应用（`Dockerfile` + `docker-compose.yml`）以便快速部署。
- 接入 CI/CD（如 GitHub Actions）：
  - Push 代码后自动运行测试；
  - 测试通过后自动构建镜像或部署到测试环境。
- 接入专业监控（Sentry、Prometheus 等），对错误、性能瓶颈进行长期跟踪。

# 部署准备指南（九、部署准备）

本指南帮助你将项目从开发环境迁移到生产环境，覆盖环境变量、依赖、静态文件、数据库迁移、进程管理、反向代理与健康检查。

## 1. 环境与依赖
- Python：建议 3.10+，确保与本地一致。
- 依赖安装：`pip install -r requirements.txt`（生产环境请使用虚拟环境）。
- 操作系统依赖：确保有编译工具链、`libpq`（如使用 PostgreSQL）、Redis 客户端（如启用缓存）。

## 2. 环境变量（复制 `ENV_TEMPLATE.md` 为 `.env`）
- 必填：`SECRET_KEY`、`ALLOWED_HOSTS`、数据库相关（`DB_NAME/USER/PASSWORD/HOST/PORT`）。
- 建议：`REDIS_URL`（缓存）、邮件配置（错误通知）、`DEBUG=False`。
- 不要将 `.env` 提交到版本库。

## 3. 使用生产配置
- 设置环境变量：`DJANGO_SETTINGS_MODULE=ll_project.settings_production`
- 或启动命令中显式指定：`python manage.py migrate --settings=ll_project.settings_production`

## 4. 静态与媒体文件
- 收集静态文件：`python manage.py collectstatic --noinput --settings=ll_project.settings_production`
- 静态目录：`STATIC_ROOT=BASE_DIR/staticfiles`
- 媒体目录：`MEDIA_ROOT=BASE_DIR/media`（请配置 Nginx 等反向代理指向该目录）
- 可选：使用 WhiteNoise 或 CDN，生产建议由 Nginx 提供静态/媒体文件。

## 5. 数据库与迁移
- 确保数据库账号、库名已创建并有权限。
- 执行迁移：`python manage.py migrate --settings=ll_project.settings_production`
- 如需创建超级用户：`python manage.py createsuperuser --settings=ll_project.settings_production`

## 6. 进程管理与启动
- 推荐：`gunicorn ll_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --settings=ll_project.settings_production`
- Windows 可使用 `waitress-serve` 或 IIS 部署；Linux 生产建议配合 systemd+Gunicorn+Nginx。
- 配置 systemd 示例（简化）：
  - `ExecStart=/path/to/venv/bin/gunicorn ll_project.wsgi:application --bind 127.0.0.1:8000 --workers 3 --settings=ll_project.settings_production`
  - `Environment=\"DJANGO_SETTINGS_MODULE=ll_project.settings_production\"`

## 7. 反向代理（Nginx 示例）
- 反代到 `127.0.0.1:8000`。
- 配置 HTTPS，启用 HTTP/2，强制跳转 HTTPS。
- 静态文件：`location /static/ { alias /path/to/staticfiles/; }`
- 媒体文件：`location /media/ { alias /path/to/media/; }`

## 8. 日志与监控
- 应用日志：`logs/django.log`（生产，滚动日志，已在 `settings_production.py` 配置）。
- 错误日志：`logs/django_error.log`。
- 控制台输出：保留基础信息，便于容器环境查看。
- 邮件告警：配置 `EMAIL_*` 与 `ADMINS`，生产异常将发送邮件。
- 监控：可选接入 Prometheus/ELK/Sentry；至少保留健康检查接口。

## 9. 健康检查与探针
- 健康检查：`/health/`（快速） `/health/detailed/`（含数据库、缓存、静态检查）
- 就绪探针：`/health/ready/`
- 存活探针：`/health/live/`
- 部署到 Kubernetes/Docker 时，可直接引用上述端点。

## 10. 安全加固清单
- `DEBUG=False`，`ALLOWED_HOSTS` 已配置。
- HTTPS 强制跳转，启用 HSTS、X-Frame-Options、X-Content-Type-Options、XSS 过滤。
- 确保 `SECRET_KEY` 不在仓库中，使用环境变量。
- 设置强密码策略与管理员账号最小化。
- 定期更新依赖，检查 CVE（可用 `pip-audit`）。

## 11. 备份与恢复
- 数据库定期备份（如 pg_dump），保留多份并存储在安全位置。
- 媒体文件定期同步到对象存储或备份盘。
- 定期验证恢复流程，确保备份可用。

## 12. 部署前快速自检
- `python manage.py check --deploy --settings=ll_project.settings_production`
- `python manage.py test --settings=ll_project.settings_production`（可选）
- `python manage.py collectstatic --noinput --settings=ll_project.settings_production`
- 日志目录存在：`logs/`
- 数据库/缓存连通性确认。

## 13. 常用命令速查
- 迁移：`python manage.py migrate --settings=ll_project.settings_production`
- 收集静态：`python manage.py collectstatic --noinput --settings=ll_project.settings_production`
- 启动：`gunicorn ll_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --settings=ll_project.settings_production`
- 健康检查：`curl http://127.0.0.1:8000/health/`

