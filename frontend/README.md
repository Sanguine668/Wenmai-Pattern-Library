# 中华纹脉 · 前端

中华传统纹样资源数据管理系统的前端展台。首页与数字人使用从已标注主数据中选出的 54 条真实记录（真实馆藏图片、原始标题、朝代、载体、来源与许可）；纹样库、详情、个人中心与后台直接读取后端全量数据库（1346 条），不使用占位图或虚构统计。

## 启动

```bash
npm install
npm run dev
```

默认地址：`http://127.0.0.1:5173`

生产构建：

```bash
npm run build
```

## 页面

- `/` 首页：博物馆图录式目录、纹样类型索引、为你推荐三图叠放、蛇形朝代时间轴（全部朝代一次展示，无横向滚动）、馆藏精选、最近整理；首屏统计读取 `/api/stats`，离线时回落到静态值；
- `/patterns` 纹样库：类型 / 朝代 / 载体三组筛选与搜索，全量 1346 条；筛选栏计数会随当前条件联动刷新（调用 `/api/facets`）；从详情返回时恢复进入前的筛选、页码与滚动位置；
- `/patterns/:id` 纹样详情：真实图片、档案信息、主色卡、同类纹样与来源；
- `/upload` 上传识别：点击、拖拽、粘贴三种入口；未配置后端时明确显示界面模式；
- `/create` 纹样创作：基础纹样 / 壁纸 / 产品应用三种模式，展示真实馆藏参考；
- `/profile` 个人中心：登录后显示本人账号，收藏与浏览记录写入账号；未登录时使用 demo 游客账号；
- `/login` 登录 / 注册：JWT 登录、普通用户注册，登录后回到原页面；
- `/admin` 编目台：**需要管理员登录**，未登录跳转 `/login?redirect=/admin`，普通用户跳转个人中心并提示无权限。

## 账号与鉴权

- 令牌保存在 `localStorage` 的 `wenmai:token`，`src/lib/api.js` 自动附加 `Authorization: Bearer`；
- 令牌失效（401）时自动清除会话并回到游客状态；
- 会话恢复：`src/lib/auth.js` 启动时调用 `GET /api/auth/me`；
- 收藏与浏览接口已迁移到 `/api/me/*`（游客自动回落到 demo 账号）；
- 退出登录、令牌失效时会清空本地收藏与浏览缓存，再同步当前身份；
- 管理员口令不写在前端：由后端首次初始化生成到 `data/admin-initial-password.txt`，或通过 `WENMAI_ADMIN_PASSWORD` 指定。

## 数据

`src/data/patterns.js` 由项目根目录的 `tools/build_frontend_data.py` 生成；54 张网页图片位于 `public/patterns/`。
首页精选、数字人本地检索、创作参考与上传示例仍使用这 54 条静态精选，不等于完整资源库。

数据库中的纹样名已从“类型 · 载体”改为文物名，纹样类型与载体在卡片、详情和后台均以标签单独展示；
名称生成脚本见 `tools/localize_names.py`（规则引擎）与 `tools/merge_name_translations.py`（批量译文合并）。

重新生成数据（在主项目根目录执行）：

```bash
python tools/build_frontend_data.py
```

## 后端接口

默认通过 Vite 代理把 `/api` 转发到 `http://127.0.0.1:8000`；如需直连，复制 `.env.example` 为 `.env`：

```bash
VITE_API_BASE=http://127.0.0.1:8000
```

未配置 `VITE_API_BASE` 时，上传页、创作页会明确提示接口未连接；数字人退化为本地档案检索，不伪造模型输出。

## 验收脚本

在项目根目录执行（需 Chrome 调试端口 9223）：

```bash
node tools/cdp_auth_check.mjs http://127.0.0.1:5173 http://127.0.0.1:9223
node tools/cdp_admin_check.mjs http://127.0.0.1:5173 http://127.0.0.1:9223
node tools/cdp_user_flow.mjs http://127.0.0.1:5173 http://127.0.0.1:9223
```
