import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, api, clearToken, getToken, saveToken } from "./api";

const FILTERS = [
  { key: "all", label: "全部" },
  { key: "active", label: "未完成" },
  { key: "done", label: "已完成" },
];

function App() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("all");
  const [authMode, setAuthMode] = useState("login");
  const [user, setUser] = useState(null);
  const [serverOnline, setServerOnline] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  const showToast = (message) => {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(""), 2600);
  };

  const signOut = () => {
    clearToken();
    setUser(null);
    setTasks([]);
  };

  const loadTasks = async () => {
    if (!getToken()) {
      setTasks([]);
      return;
    }

    try {
      setTasks(await api.listTasks());
    } catch (error) {
      signOut();
      showToast(error.message);
    }
  };

  useEffect(() => {
    api.health()
      .then(() => setServerOnline(true))
      .catch(() => setServerOnline(false));

    if (!getToken()) return;

    api.me()
      .then((currentUser) => {
        setUser(currentUser);
        return loadTasks();
      })
      .catch((error) => {
        signOut();
        showToast(error.message);
      });
  }, []);

  const visibleTasks = useMemo(
    () =>
      tasks.filter((task) => {
        if (filter === "active") return !task.completed;
        if (filter === "done") return task.completed;
        return true;
      }),
    [filter, tasks],
  );

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const username = form.get("username").trim();
    const password = form.get("password");
    setAuthLoading(true);

    try {
      if (authMode === "register") {
        await api.register(username, password);
        setAuthMode("login");
        showToast("注册成功，请登录");
        event.currentTarget.reset();
        return;
      }

      const result = await api.login(username, password);
      saveToken(result.access_token);
      setUser(await api.me());
      event.currentTarget.reset();
      await loadTasks();
      showToast("登录成功");
    } catch (error) {
      showToast(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleCreateTask = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = form.get("title").trim();
    if (!title) return;

    try {
      await api.createTask({
        title,
        description: form.get("description").trim() || null,
      });
      event.currentTarget.reset();
      await loadTasks();
    } catch (error) {
      showToast(error.message);
    }
  };

  const handleToggleTask = async (task) => {
    const completed = !task.completed;
    setTasks((current) =>
      current.map((item) => (item.id === task.id ? { ...item, completed } : item)),
    );

    try {
      await api.updateTask(task.id, { completed });
    } catch (error) {
      setTasks((current) =>
        current.map((item) =>
          item.id === task.id ? { ...item, completed: task.completed } : item,
        ),
      );
      showToast(error.message);
    }
  };

  const handleDeleteTask = async (task) => {
    setTasks((current) => current.filter((item) => item.id !== task.id));

    try {
      await api.deleteTask(task.id);
    } catch (error) {
      showToast(error.message);
      await loadTasks();
    }
  };

  const activeCount = tasks.filter((task) => !task.completed).length;
  const isRegistering = authMode === "register";

  return (
    <div className="wrap">
      <header>
        <div>
          <h1>Tasks</h1>
          <p className="sub">FastAPI · React 前端</p>
        </div>
        <span className={`status ${serverOnline ? "online" : "offline"}`}>
          <span className="dot" />
          <span>{serverOnline ? "API 已连接" : "API 未连接"}</span>
        </span>
      </header>

      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="auth-header">
          <div>
            <h2 className="auth-title" id="auth-title">
              {user ? "已登录" : isRegistering ? "注册" : "登录"}
            </h2>
            <p className="auth-hint">
              {user
                ? "当前账号只能看到自己创建的任务"
                : isRegistering
                  ? "创建账号后即可开始管理任务"
                  : "登录后管理属于你的任务"}
            </p>
          </div>
          {user && (
            <div className="auth-user">
              <span>
                当前用户：<strong>{user.username}</strong>
              </span>
              <button className="logout" type="button" onClick={signOut}>
                退出
              </button>
            </div>
          )}
        </div>

        {!user && (
          <>
            <form className="auth-form" onSubmit={handleAuthSubmit}>
              <input
                name="username"
                type="text"
                placeholder="用户名（3-50 个字符）"
                minLength="3"
                maxLength="50"
                autoComplete="username"
                required
              />
              <input
                name="password"
                type="password"
                placeholder="密码（至少 6 个字符）"
                minLength="6"
                maxLength="100"
                autoComplete={isRegistering ? "new-password" : "current-password"}
                required
              />
              <button className="auth-submit" type="submit" disabled={authLoading}>
                {isRegistering ? "注册" : "登录"}
              </button>
            </form>
            <button
              className="auth-switch"
              type="button"
              onClick={() => setAuthMode(isRegistering ? "login" : "register")}
            >
              {isRegistering ? "已有账号？登录" : "还没有账号？注册"}
            </button>
          </>
        )}
      </section>

      {user && (
        <main>
          <form className="composer" onSubmit={handleCreateTask}>
            <input name="title" type="text" placeholder="要做什么？" maxLength="100" autoComplete="off" required />
            <textarea name="description" placeholder="补充说明（可选）" rows="1" maxLength="2000" />
            <div className="composer-row">
              <span className="hint">输入任务后提交</span>
              <button className="add" type="submit">添加任务</button>
            </div>
          </form>

          <div className="toolbar">
            <div className="filters" role="tablist" aria-label="任务筛选">
              {FILTERS.map((item) => (
                <button
                  className={`filter ${filter === item.key ? "active" : ""}`}
                  data-filter={item.key}
                  key={item.key}
                  type="button"
                  onClick={() => setFilter(item.key)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <span className="count">{tasks.length} 项 · {activeCount} 未完成</span>
          </div>

          <div className="list">
            {!visibleTasks.length && (
              <div className="empty">
                <strong>{tasks.length ? "这个分类下没有任务" : "还没有任务"}</strong>
                <span>{tasks.length ? "换个筛选条件看看" : "在上面输入第一条任务"}</span>
              </div>
            )}
            {visibleTasks.map((task) => (
              <article className={`task ${task.completed ? "done" : ""}`} key={task.id}>
                <button
                  className={`check ${task.completed ? "checked" : ""}`}
                  type="button"
                  aria-label={task.completed ? "标记为未完成" : "标记为完成"}
                  onClick={() => handleToggleTask(task)}
                />
                <div className="body">
                  <p className="title">{task.title}</p>
                  {task.description && <p className="desc">{task.description}</p>}
                </div>
                <button
                  className="del"
                  type="button"
                  aria-label="删除任务"
                  onClick={() => handleDeleteTask(task)}
                >
                  ×
                </button>
              </article>
            ))}
          </div>
        </main>
      )}

      <footer>
        <span>API：<code>/auth</code></span>
        <span><code>/tasks</code></span>
        <span>后端文档：<a href={`${API_BASE_URL}/docs`}>Swagger</a></span>
      </footer>

      <div className={`toast ${toastMessage ? "show" : ""}`}>{toastMessage}</div>
    </div>
  );
}

export default App;
