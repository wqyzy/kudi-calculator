# ☕ 库迪咖啡 · 在线协作财务计算器 — 部署指南

## 项目结构

```
kudi-online/
├── app.py              # Flask 后端
├── requirements.txt    # Python 依赖
├── data.db             # SQLite 数据库（自动生成）
└── templates/
    ├── index.html      # 首页（创建/加入项目）
    └── calculator.html # 计算器页面（含协作功能）
```

---

## 方式一：一键部署到 Render（推荐，免费）

### 步骤

1. **注册 Render 账号**
   - 打开 https://render.com
   - 用 GitHub 或 Google 账号注册（免费）

2. **上传代码到 GitHub**
   - 在你的 GitHub 新建仓库，把 `kudi-online/` 文件夹里的内容传上去

3. **在 Render 创建 Web Service**
   - 点击 `New +` → `Web Service`
   - 连接你的 GitHub 仓库
   - 填写：
     - **Name**: `kudi-calculator`（随便写）
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
   - 计划选 **Free**（免费额度够用）
   - 点击 `Create Web Service`

4. **等待部署完成**（约2-3分钟）
   - 部署成功后，你会得到一个链接，如：`https://kudi-calculator.onrender.com`
   - 打开这个链接就能用了

---

## 方式二：部署到 Railway（备选，免费）

1. 注册 https://railway.app
2. 新建项目 → `Deploy from GitHub repo`
3. 上传代码 → 连接仓库
4. 添加环境变量（如果有需要）
5. Railway 会自动检测 `requirements.txt` 并部署

---

## 使用方式

### 协作流程

```
你： 创建项目 → 填租金、客流等数据 → 把分享码发给对方
对方： 打开链接 → 输入分享码 → 填人工、成本等数据
你们： 各自填完自动保存 → 互相刷新就能看到完整结果
```

### 具体操作

1. **打开首页** → 点击「创建项目」
2. **填写你掌握的数据**（比如租金、客流量）
3. **复制顶部的6位分享码**（如 `XM3K9P`）发给对方
4. **对方打开首页** → 点击「加入项目」→ 输入分享码
5. **对方填写另一部分数据**（比如设备费、人工成本）
6. **任何修改自动保存到云端**（3秒延迟）
7. **页面每15秒自动刷新云端数据**，对方填的内容会自动同步过来
8. **结果实时计算**，双方看到的计算结果是一致的

---

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（开发模式）
python app.py

# 或者用 gunicorn（生产模式）
gunicorn app:app

# 打开浏览器访问
# http://localhost:5000
```

---

## 注意事项

- SQLite 数据库存在服务本地，免费版 Render 每月有 512MB 存储，完全够用
- 数据纯属数字，**不收集任何个人信息**
- 如果用量大，可以考虑升级到付费版，或换成 PostgreSQL
- 同一个分享码可以多人同时编辑，数据以最后一次保存为准
