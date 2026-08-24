def test_get_items_requires_authentication(client):
    response = client.get("/items")

    assert response.status_code == 401


def test_post_items_requires_authentication(client):
    response = client.post(
        "/items",
        json={
            "name": "test-item",
            "quantity": 1,
        },
    )

    assert response.status_code == 401
