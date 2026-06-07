# 711-code 项目说明

这是一个由三个子项目组成的本地演示仓库，核心目标是提供“慢游 / 出游规划”相关的前端界面、业务后端，以及 AI 路线规划能力。

## 目录结构

```text
711-code/
├── 711-frontend/   Flutter 前端
├── backend/        FastAPI 业务后端
├── 711-AI/         Git submodule：FastAPI + LangGraph AI 路线规划服务
└── README.md
```

## 克隆说明

`711-AI` 现在作为 Git submodule 挂在主仓库中。首次拉取项目后，请执行：

```bash
git submodule update --init --recursive
```

如果你是首次克隆整个仓库，也可以直接使用：

```bash
git clone --recurse-submodules git@github.com:LisazhenYANG/711-code.git
```

## 模块说明

### 1. `711-frontend`

- 技术栈：Flutter
- 作用：提供移动端原型界面，包含路线生成、路线查看、附近推荐、预约清单、个人偏好等流程
- 主要依赖的服务：
  - `backend`：业务接口，默认 `http://127.0.0.1:8000`
  - `711-AI`：AI 规划与餐厅相关接口，默认 `http://127.0.0.1:8001`

前端使用的是 `String.fromEnvironment`，因此配置项需要通过 `--dart-define` 传入，而不是自动读取 `.env` 文件。仓库中的 `.env.example` 仅作为配置模板参考。

### 2. `backend`

- 技术栈：FastAPI
- 作用：承接前端业务流程，提供仪表盘、路线生成、预约结算、行程保存、反馈写回等接口
- 默认端口：`8000`
- 健康检查：`GET /api/health`

当前后端会把部分本地状态写入 SQLite，默认数据库文件位于：

```text
backend/data/manyou.sqlite3
```

也可以通过环境变量 `MANYOU_DB_PATH` 自定义数据库路径。

### 3. `711-AI`

- 技术栈：FastAPI、LangGraph
- 作用：提供路线规划、反馈回写、餐厅查询、排队取号、订座等 AI / 智能能力
- 默认端口：`8001`
- 健康检查：`GET /health`
- 仓库形态：作为主仓库的 Git submodule 管理

该服务支持 `.env` 配置，已提供 `.env.example` 模板。若接入真实 LLM 或地图服务，需要在本地 `.env` 中填写对应密钥。

## 环境变量模板

仓库当前包含以下示例配置文件：

- [`711-AI/.env.example`](/Users/lisa/Desktop/hackthon/711-code/711-AI/.env.example)
- [`backend/.env.example`](/Users/lisa/Desktop/hackthon/711-code/backend/.env.example)
- [`711-frontend/.env.example`](/Users/lisa/Desktop/hackthon/711-code/711-frontend/.env.example)

建议做法：

```bash
cp 711-AI/.env.example 711-AI/.env
cp backend/.env.example backend/.env
```

前端如果要运行 Web 版，可以把配置项通过 `--dart-define` 传入，例如：

```bash
flutter run -d chrome \
  --dart-define=MANYOU_API_BASE_URL=http://127.0.0.1:8000 \
  --dart-define=MANYOU_AI_BASE_URL=http://127.0.0.1:8001 \
  --dart-define=AMAP_WEB_KEY=your_amap_web_key \
  --dart-define=AMAP_SECURITY_CODE=your_amap_security_code
```

## 本地启动顺序

推荐按下面顺序启动：

### 1. 启动 `backend`

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. 启动 `711-AI`

```bash
cd 711-AI
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

如果需要真实 LLM 能力，请先复制 `.env.example` 并补齐本地密钥。

### 3. 启动 `711-frontend`

```bash
cd 711-frontend
flutter pub get
flutter run -d chrome \
  --dart-define=MANYOU_API_BASE_URL=http://127.0.0.1:8000 \
  --dart-define=MANYOU_AI_BASE_URL=http://127.0.0.1:8001
```

## 常用接口

### `backend`

- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/routes/generate`
- `POST /api/bookings/checkout`
- `POST /api/trips`
- `GET /api/trips`
- `POST /api/feedback`

### `711-AI`

- `GET /health`
- `POST /plan`
- `POST /feedback`
- `GET /restaurants`
- `GET /restaurants/{id}/queue`
- `POST /booking/queue`
- `POST /booking/reservation`

## Git 说明

仓库根目录已经补充 `.gitignore`，当前会忽略：

- Python 缓存与虚拟环境
- Flutter / Dart 构建产物
- `.claude` 本地配置
- `.env` 等本地敏感配置
- SQLite 本地数据库

同时保留 `.env.example` 这类示例模板文件，便于团队协作。
