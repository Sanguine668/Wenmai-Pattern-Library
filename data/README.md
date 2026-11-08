# 本期示例数据说明

仓库自带一份**最小可用数据集**：55 条从主数据中选出的已标注记录，覆盖瓷器、织锦、漆器、玉器、金属器、壁画等载体，图片均为随仓库分发的本地 JPG，可直接浏览、搜索、筛选、收藏和进后台编辑。

- 数据库：`data/wenmai.db`（SQLite）
- 图片：`frontend/public/patterns/*.jpg`，由数据库中的图片记录指向该相对路径
- 账号：数据库内不含用户；首次启动会自动创建 `admin` 与 `demo` 两个账号
  - 管理员密码：首次启动时读取 `WENMAI_ADMIN_PASSWORD`，未配置则生成随机密码到 `data/admin-initial-password.txt`
  - `demo` 是游客兜底账号，无密码，不能登录后台

## 从完整数据恢复

完整资源库为 1346 条记录、1311 张图片，原始图片在 `annotation_packages/` 下，体积约 4GB，不适合直接放进 GitHub 仓库。因此本仓库只带 55 条示例。

如果本地已有原始标注包，可按 `backend/README.md` 中的数据导入方式，将 `data_master/all_records_final_annotated.csv` 与 `annotation_packages/` 放回项目根目录后重新导入；也可以直接用完整数据库替换 `data/wenmai.db`。

## 重新生成示例库

示例库由主数据库筛选 55 条精选记录生成；图片路径被改写为 `frontend/public/patterns/<id>.jpg`，以保证在无 `annotation_packages/` 的机器上也能正常显示图片。
