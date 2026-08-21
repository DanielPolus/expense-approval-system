def register_user(client, email="employee@test.com", password="strong-password"):
    return client.post("/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "phone": "+40730000000",
        "password": password,
    })


def login_user(client, email="employee@test.com", password="strong-password"):
    return client.post("/auth/login", data={
        "username": email,
        "password": password,
    })


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json()["email"] == "employee@test.com"
    assert response.json()["role"] == "employee"
    assert "hashed_password" not in response.json()


def test_register_duplicate_email(client):
    register_user(client)
    response = register_user(client)

    assert response.status_code == 409


def test_login(client):
    register_user(client)
    response = login_user(client)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    register_user(client)

    response = login_user(
        client,
        password="wrong-password",
    )

    assert response.status_code == 401


def test_get_current_user(client):
    register_user(client)

    login_response = login_user(client)
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "employee@test.com"
    