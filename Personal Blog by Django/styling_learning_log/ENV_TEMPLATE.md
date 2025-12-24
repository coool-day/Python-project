# 环境变量示例（复制为 `.env` 后再填写）

## 基础配置
SECRET_KEY=请替换为生产环境的随机密钥
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,example.com

## 数据库（PostgreSQL 示例）
DB_NAME=learning_log
DB_USER=ll_user
DB_PASSWORD=please_change_me
DB_HOST=127.0.0.1
DB_PORT=5432

## Redis（可选）
REDIS_URL=redis://127.0.0.1:6379/1

## 邮件（用于错误通知）
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=no-reply@example.com
EMAIL_HOST_PASSWORD=please_change_me
DEFAULT_FROM_EMAIL=no-reply@example.com
ADMIN_NAME=Admin
ADMIN_EMAIL=admin@example.com

## 时区与语言
TIME_ZONE=Asia/Shanghai
LANGUAGE_CODE=zh-hans

