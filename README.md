# django_talk
一个基于 Django 的电商评论洞察系统，包含评论管理、数据可视化、AI 助力的洞察报告与导出功能。UI 风格参考 Otsuka THE DAY 品牌（黑白对比 + 柠檬绿点缀）。

## 功能特性
- 仪表板总览：总评论数、评分分布、情感分布、趋势图
- 评论管理：分页、筛选（产品/评分/情感/搜索）
- 洞察报告：商品口碑分、推荐等级、优缺点、关键词、可下载 Markdown 报告
- 主题聚类：可选 `jieba` + `scikit-learn` 提升中文分词与聚类质量（无则降级到简单模式）
- API 提供：评论列表、仪表板统计、评论导入

## 环境要求
- Python 3.10+（推荐 3.10 或 3.11）
- Windows、macOS 或 Linux

## 一分钟快速启动（Windows PowerShell）
## !!!注意先安装python环境，然后在firstdemo文件夹中执行以下命令
```powershell
pip install django==5.2.8 jieba scikit-learn
python manage.py runserver
```
打开浏览器访问：`http://127.0.0.1:8000/`（首页），以及：
- `http://127.0.0.1:8000/reviews/` 仪表演示页
- `http://127.0.0.1:8000/reviews/analytics/` 数据分析页
- `http://127.0.0.1:8000/reviews/insight/<product_id>/` 商品洞察报告页
- `http://127.0.0.1:8000/admin/` 管理后台

## 详细安装步骤(下面作参考)
### 1. 克隆或获取代码
确保代码路径为：`*\django\firstdemo`。

### 2. 创建并激活虚拟环境
- Windows（PowerShell）：
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- macOS/Linux（bash/zsh）：
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. 安装依赖
项目核心仅依赖 Django；为更好的中文文本聚类，建议安装：
```bash
pip install django==5.2.8 jieba scikit-learn
```
未安装 `jieba/scikit-learn` 时，系统会自动降级到简单模式，功能可用但效果稍弱。

### 4. 初始化数据库
默认使用 SQLite（文件位于 `firstdemo/db.sqlite3`）：
```bash
python manage.py migrate
```

### 5. 生成示例数据（可选但推荐）
```bash
python manage.py create_sample_data --products 5 --reviews 50
```
这会创建 5 个产品与每个 50 条评论，并自动生成洞察。

### 6. 运行开发服务器
```bash
python manage.py runserver
```
访问路径：
- `/` 首页（`Hello World`）
- `/reviews/` 仪表演示页（功能导航 + API 可用性）
- `/reviews/analytics/` 数据分析页（趋势、主题矩阵等）
- `/reviews/insight/<product_id>/` 商品洞察报告页（含 AI 建议与可视化）
- `/admin/` 管理后台

## 可选：切换到 PostgreSQL/MySQL
项目支持通过环境变量配置数据库（参考 `firstdemo/firstdemo/settings.py`）：
- `DB_ENGINE`（示例：`django.db.backends.postgresql` 或 `django.db.backends.mysql`）
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
在启动前设置环境变量即可：
```powershell
$env:DB_ENGINE = "django.db.backends.postgresql"
$env:DB_NAME   = "e_insight"
$env:DB_USER   = "postgres"
$env:DB_PASSWORD = "your_password"
$env:DB_HOST   = "127.0.0.1"
$env:DB_PORT   = "5432"
python manage.py migrate
python manage.py runserver
```

## 常用命令
- 创建管理员账号：
  ```bash
  python manage.py createsuperuser
  ```
- 运行基本检查：
  ```bash
  python manage.py check
  ```

## 主要目录结构
- `firstdemo/manage.py` Django 管理入口
- `firstdemo/firstdemo/settings.py` 项目配置（静态资源、数据库、INSTALLED_APPS）
- `firstdemo/review_insights/` 评论洞察应用（模型、视图、命令、NLP）
- `firstdemo/templates/` 模板目录（`base.html`、`review_insights/*`）
- `firstdemo/static/` 静态资源（`css/style.css`、`js/main.js`）

## API 速览
- `GET /reviews/api/dashboard/stats/` 仪表板统计
- `GET /reviews/api/reviews/?page=1&product=&rating=&sentiment=&search=` 评论列表（分页/筛选）
- `POST /reviews/api/reviews/import/` 导入评论（JSON 数组 `items`）

请求体示例：
```json
[
  {
    "product_name": "iPhone 15 Pro",
    "author": "张三",
    "content": "物流很快，做工不错",
    "rating": 5,
    "sentiment": "positive",
    "confidence": 0.9,
    "created_at": "2025-12-11T22:11:00"
  }
]
```

## 视觉风格说明
- 品牌主色：`#c8d900`（`--brand-primary`）
- 主文本色：`#080604`（`--brand-secondary`）
- 悬停动效：统一 `u-hover`（轻微上移 + 亮度提升）
- 英雄按钮：`btn-hero` / `btn-hero-outline`

## 常见问题
- 端口占用：`runserver` 报错时换端口 `python manage.py runserver 0.0.0.0:8001`
- 中文分词无效：安装 `jieba` 后重试；聚类质量提升需安装 `scikit-learn`
- 静态资源未加载：确认 `STATICFILES_DIRS = [ BASE_DIR / 'static' ]` 已生效

---