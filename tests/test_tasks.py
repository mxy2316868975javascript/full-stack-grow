import logging

from .test_auth import login, register


def create_task(client, token: str, title: str, priority: int = 1):
    """使用指定用户的 token 创建任务。"""

    return client.post(
        "/tasks",
        json={"title": title, "priority": priority},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_unauthenticated_user_cannot_list_tasks(client):
    """没有 token 时不能访问任务列表。"""

    response = client.get("/tasks")

    assert response.status_code == 401


def test_requests_write_basic_access_logs(client, caplog):
    """请求日志应包含方法、路径和状态码，不依赖业务响应内容。"""

    with caplog.at_level(logging.INFO, logger="task_api"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any(
        "request method=GET path=/health status=200" in record.getMessage()
        for record in caplog.records
    )


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

    assert alice_tasks.json()["total"] == 1
    assert bob_tasks.json()["total"] == 1
    assert [task["title"] for task in alice_tasks.json()["items"]] == ["Alice task"]
    assert [task["title"] for task in bob_tasks.json()["items"]] == ["Bob task"]


def test_tasks_are_paginated(client):
    """任务列表应按页返回，并提供总数和总页数。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")

    for index in range(25):
        response = create_task(client, token, f"Task {index + 1}")
        assert response.status_code == 201

    response = client.get(
        "/tasks?page=2&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 10
    assert response.json()["total"] == 25
    assert response.json()["pages"] == 3
    assert [task["title"] for task in response.json()["items"]] == [
        f"Task {index}" for index in range(11, 21)
    ]


def test_task_pagination_parameters_are_validated(client):
    """页码和每页数量超出范围时应由 FastAPI 返回 422。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/tasks?page=0", headers=headers).status_code == 422
    assert client.get("/tasks?page_size=101", headers=headers).status_code == 422


def test_tasks_can_be_filtered(client):
    """任务列表应支持完成状态、优先级和组合筛选。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")
    headers = {"Authorization": f"Bearer {token}"}

    completed_task = create_task(client, token, "Completed", priority=2).json()
    active_task = create_task(client, token, "Active", priority=3).json()
    client.patch(
        f"/tasks/{completed_task['id']}",
        json={"completed": True},
        headers=headers,
    )

    completed = client.get("/tasks?completed=true", headers=headers)
    priority = client.get("/tasks?priority=3", headers=headers)
    combined = client.get(
        "/tasks?completed=false&priority=3",
        headers=headers,
    )

    assert completed.json()["total"] == 1
    assert completed.json()["items"][0]["title"] == "Completed"
    assert priority.json()["total"] == 1
    assert priority.json()["items"][0]["title"] == "Active"
    assert combined.json()["total"] == 1
    assert combined.json()["items"][0]["title"] == "Active"


def test_task_filter_parameters_are_validated(client):
    """优先级超出任务模型范围时应由 FastAPI 返回 422。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")

    assert client.get(
        "/tasks?priority=6",
        headers={"Authorization": f"Bearer {token}"},
    ).status_code == 422


def test_tasks_can_be_sorted(client):
    """任务列表应支持安全的字段排序和排序方向。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")
    headers = {"Authorization": f"Bearer {token}"}

    low_priority = create_task(client, token, "Low", priority=1).json()
    high_priority = create_task(client, token, "High", priority=5).json()
    client.patch(
        f"/tasks/{low_priority['id']}",
        json={"completed": True},
        headers=headers,
    )

    by_priority = client.get(
        "/tasks?sort_by=priority&order=desc",
        headers=headers,
    )
    by_completed = client.get(
        "/tasks?sort_by=completed&order=desc",
        headers=headers,
    )

    assert [task["title"] for task in by_priority.json()["items"]] == [
        "High",
        "Low",
    ]
    assert [task["title"] for task in by_completed.json()["items"]] == [
        "Low",
        "High",
    ]


def test_task_sort_parameters_are_validated(client):
    """不在白名单内的排序字段和方向应返回 422。"""

    register(client, "alice", "alice123")
    token = login(client, "alice", "alice123")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get(
        "/tasks?sort_by=owner_id",
        headers=headers,
    ).status_code == 422
    assert client.get(
        "/tasks?order=random",
        headers=headers,
    ).status_code == 422


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
