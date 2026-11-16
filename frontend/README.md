# Task Web

这是独立的 Vite + React 前端，后端 API 位于项目根目录。

## 本地开发

```bash
cd frontend
cp .env.example .env
pnpm install
pnpm dev
```

默认页面地址是 `http://localhost:5173`，API 地址由 `VITE_API_BASE_URL` 配置，默认是 `http://127.0.0.1:8000`。

如果后端使用 `APP_PORT=8001` 启动，把 `.env` 中的地址改成 `http://127.0.0.1:8001`。

后端需要先启动，并且 `CORS_ORIGINS` 要包含前端页面的来源。

## 生产构建

```bash
pnpm build
pnpm preview
```

`src/api.js` 统一处理 API 基础地址、JWT 请求头和错误响应；`src/App.jsx` 负责页面状态和任务交互；`src/styles.css` 负责视觉样式。
