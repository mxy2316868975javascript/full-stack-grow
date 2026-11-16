export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "task_api_token";

export function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request(path, options = {}) {
  const { skipAuth = false, ...fetchOptions } = options;
  const headers = { ...(fetchOptions.headers || {}) };
  const token = getToken();

  if (fetchOptions.body !== undefined && !(fetchOptions.body instanceof URLSearchParams)) {
    headers["Content-Type"] ||= "application/json";
  }
  if (token && !skipAuth) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (response.status === 401 && path !== "/auth/login") {
    clearToken();
    throw new Error("登录已过期，请重新登录");
  }

  if (!response.ok) {
    let message = `请求失败（${response.status}）`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
      if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        message = data.detail[0].msg;
      }
    } catch {
      // 非 JSON 错误响应使用默认提示。
    }
    throw new Error(message);
  }

  return response.status === 204 ? null : response.json();
}

export const api = {
  health: () => request("/health", { skipAuth: true }),
  register: (username, password) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  login: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username, password }),
    }),
  me: () => request("/auth/me"),
  listTasks: () => request("/tasks"),
  createTask: (payload) =>
    request("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTask: (taskId, payload) =>
    request(`/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteTask: (taskId) => request(`/tasks/${taskId}`, { method: "DELETE" }),
};
