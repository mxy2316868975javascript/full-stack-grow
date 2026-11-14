from .test_auth import login, register


def create_task(client, token: str, title: str):
    """使用指定用户的 token 创建任务。"""

    return client.post(
        "/tasks",
        json={"title": title, "priority": 1},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_unauthenticated_user_cannot_list_tasks(client):
    """没有 token 时不能访问任务列表。"""

    response = client.get("/tasks")

    assert response.status_code == 401


def test_users_only_see_their_own_tasks(client):
    """不同用户只能看到自己创建的任务。"""

    assert register(client, "alice", "alice123").status_code == 201
    assert register(client, "bob", "bob12345").status_code == 201

    alice_token = login(client, "alice", "alice123")
    bob_token = login(client, "bob", "bob12345")

    alice_task = create_task(client, alice_token, "Alice task")
    bob_task = create_task(client, bob_token, "Bob task")

    assert alice_task.status_code == 201
    assert bob_task.status_code == 201

    alice_tasks = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    bob_tasks = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    assert [task["title"] for task in alice_tasks.json()] == ["Alice task"]
    assert [task["title"] for task in bob_tasks.json()] == ["Bob task"]


def test_user_cannot_update_or_delete_another_users_task(client):
    """任务详情、更新和删除都必须检查所属用户。"""

    register(client, "alice", "alice123")
    register(client, "bob", "bob12345")
    alice_token = login(client, "alice", "alice123")
    bob_token = login(client, "bob", "bob12345")
    task_id = create_task(client, alice_token, "Alice task").json()["id"]

    headers = {"Authorization": f"Bearer {bob_token}"}
    get_response = client.get(f"/tasks/{task_id}", headers=headers)
    patch_response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Hijacked task"},
        headers=headers,
    )
    delete_response = client.delete(f"/tasks/{task_id}", headers=headers)

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
    assert delete_response.status_code == 404
