# 中华纹脉后端

FastAPI + SQLAlchemy 的资源数据服务。默认使用项目内 SQLite 持久化文件，
也可通过 `DATABASE_URL` 切换为 MySQL。首次启动会自动建表并导入
`data_master/all_records_final_annotated.csv`，包括全部资源、1311 张图片关联、
标签、演示用户与管理员账号、收藏及浏览记录。

## 启动

```powershell
.\backend\start_backend.ps1
```

服务地址：`http://127.0.0.1:8000`

接口文档：`http://127.0.0.1:8000/docs`

## 鉴权与账号（2026-11-08 起）

- 令牌：JWT（HS256），请求头 `Authorization: Bearer <token>`，默认有效期 720 分钟；
- 令牌载荷含密码指纹，**修改密码后旧令牌立即失效**；
- 密码：bcrypt 加盐哈希；历史裸 SHA-256 记录会在登录成功时自动升级；
- 启动时幂等维护两个基础账号：
  - `demo`：游客兜底账号，无密码、永远不是管理员，不能删除或修改权限；
  - `admin`：管理员账号。**代码中不内置口令**：
    - 首次创建时读取 `WENMAI_ADMIN_PASSWORD`；
    - 未配置则生成随机口令并写入 `data/admin-initial-password.txt`；
    - 已存在账号不会被启动流程改动，改密请用下方命令。
- 登录失败限速：同一账号 + IP 在窗口期内连续失败 5 次后返回 429（`Retry-After`）。

### 管理员口令维护

```powershell
cd backend
python -m app.admin_tool set-password --generate   # 生成随机口令并写入 data/admin-initial-password.txt
python -m app.admin_tool set-password --password 你的新口令
```

### 认证接口

| 方法与路径 | 说明 |
|---|---|
| `POST /api/auth/register` | 注册普通用户，返回 `{token, user}` |
| `POST /api/auth/login` | 用户名密码登录，返回 `{token, user}` |
| `GET /api/auth/me` | 当前登录用户（需令牌） |

### 权限矩阵

| 接口 | 匿名 | 普通用户 | 管理员 |
|---|---|---|---|
| `/api/health`、`/api/stats`、`/api/meta`、`/api/tags` | 允许 | 允许 | 允许 |
| `GET /api/patterns`、`/api/patterns/{id}`、`/api/images/{id}` | 允许 | 允许 | 允许 |
| `POST/PATCH/DELETE /api/patterns` | 401 | 403 | 允许 |
| `GET/POST /api/users` | 401 | 403 | 允许 |
| `GET/PATCH/DELETE /api/users/{id}` | 401 | 仅本人（不能改权限字段） | 允许 |
| `/api/users/{id}/favorites`、`/views`、`/history` | 401 | 仅本人 | 允许 |
| `/api/me/favorites`、`/api/me/history`、`/api/me/views/{pattern_id}` | 回落到 demo 游客 | 本人 | 本人 |

附加规则：不能删除自己；不能取消自己的管理员身份或停用自己；`demo` 不能删除。

## 主要接口

- `GET /api/patterns`：分页、搜索与组合筛选（`keyword/motif/dynasty/carrier/source/status/has_image/sort/limit/offset`，limit 上限 100）
  - `keyword` 同时匹配名称、原始标题、描述、来源编号、纹样类型与载体；纹样名现在为文物名，类型/载体以标签形式展示
- `GET /api/patterns/{id}`：详情与相关纹样
- `GET /api/images/{image_id}`：返回真实图片文件；`.tif/.tiff`（敦煌壁画）会自动转成 JPEG 并缓存到 `data/image_cache/`
- `GET /api/stats`、`GET /api/meta`、`GET /api/facets`、`GET /api/tags`
  - `/api/facets` 返回当前筛选条件下的类型 / 朝代 / 载体计数（自身维度不参与过滤），供筛选栏联动显示
- 纹样与用户 CRUD、收藏、浏览记录（见上表权限）

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | 项目内 `data/wenmai.db` | 数据库连接串，可切 MySQL |
| `WENMAI_JWT_SECRET` | 自动生成并保存到 `data/.jwt_secret` | 令牌签名密钥，生产必须显式配置（≥32 字符） |
| `WENMAI_TOKEN_MINUTES` | `720` | 令牌有效期（分钟） |
| `WENMAI_ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `WENMAI_ADMIN_PASSWORD` | 空 | 管理员初始密码；为空时首次创建随机生成到 `data/admin-initial-password.txt` |
| `WENMAI_ADMIN_DISPLAY_NAME` | `系统管理员` | 管理员显示名 |
| `WENMAI_ADMIN_EMAIL` | `admin@wenmai.local` | 管理员邮箱（仅首次创建生效） |
| `WENMAI_LOGIN_MAX_ATTEMPTS` | `5` | 登录失败锁定阈值 |
| `WENMAI_LOGIN_WINDOW_SECONDS` | `900` | 登录失败统计窗口（秒） |
| `DEMO_USERNAME` | `demo` | 游客兜底账号用户名 |

## 测试

```powershell
# 在项目根目录
python -m pytest backend/tests -q

# 或进入 backend 目录
python -m pytest
```

测试使用临时 SQLite，不会读写 `data/wenmai.db`。测试依赖见
`requirements-dev.txt`（pytest、httpx）。

## 数据与导入

默认数据库文件为 `data/wenmai.db`，首次启动会从主数据 CSV 导入全部记录。
重新全量导入前请先备份数据库：

```powershell
cd backend
python -m app.importer --reset
```

## 已知限制

- 令牌为无状态 JWT，服务端不维护吊销列表；退出登录仅清除前端令牌，改密可使旧令牌失效；
- 游客的收藏与浏览记录写入共享的 `demo` 账号；
- 登录失败限速保存在进程内存中，多 worker 部署时不共享；
- 暂未实现验证码、操作审计日志；
- 暂无 Alembic 迁移，新增字段需要手工迁移或重建数据库。
