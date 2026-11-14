def register(client, username: str, password: str):
    """调用注册接口，减少测试中的重复请求代码。"""

    return client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )


def login(client, username: str, password: str) -> str:
    """登录并返回 Bearer token。"""

    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_login_and_get_current_user(client):
    """注册、登录和获取当前用户应当形成完整链路。"""

    response = register(client, "alice", "alice123")

    assert response.status_code == 201
    assert response.json()["username"] == "alice"

    token = login(client, "alice", "alice123")
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_duplicate_username_returns_conflict(client):
    """重复用户名应当返回 409，而不是创建第二个用户。"""

    register(client, "alice", "alice123")
    response = register(client, "alice", "different123")

    assert response.status_code == 409


def test_wrong_password_returns_unauthorized(client):
    """密码错误时登录应当返回 401。"""

    register(client, "alice", "alice123")
    response = client.post(
        "/auth/login",
        data={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
