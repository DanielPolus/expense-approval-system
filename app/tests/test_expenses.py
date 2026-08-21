from sqlalchemy import select
from app.models.user import User, UserRole
from decimal import Decimal


def register_user(client, email, password="strong-password"):
    response = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "phone": None,
        "password": password,
    })

    assert response.status_code == 201

    return response


def login_user(client, email, password="strong-password"):
    response = client.post("/auth/login", data={
        "username": email,
        "password": password,
    })

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def change_role(db, email, role):
    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    assert user is not None

    user.role = role
    db.commit()


def create_expense(client, token):
    return client.post(
        "/expenses",
        headers=auth_headers(token),
        json={
            "title": "Business trip",
            "details": "Hotel accommodation",
            "amount": 450.50,
            "currency": "EUR",
            "category": "travel",
        },
    )


def test_employee_can_create_expense(client):
    register_user(client, "employee@test.com")
    token = login_user(client, "employee@test.com")

    response = create_expense(client, token)

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert Decimal(response.json()["amount"]) == Decimal("450.50")


def test_employee_sees_only_own_expenses(client):
    register_user(client, "first@test.com")
    register_user(client, "second@test.com")

    first_token = login_user(client, "first@test.com")
    second_token = login_user(client, "second@test.com")

    create_expense(client, first_token)
    create_expense(client, second_token)

    response = client.get(
        "/expenses",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_full_expense_lifecycle(client, db):
    register_user(client, "employee@test.com")
    employee_token = login_user(client, "employee@test.com")

    create_response = create_expense(
        client,
        employee_token,
    )

    assert create_response.status_code == 201

    expense_id = create_response.json()["id"]

    update_response = client.patch(
        f"/expenses/{expense_id}",
        headers=auth_headers(employee_token),
        json={
            "amount": 500.00
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["amount"] == "500.00"

    submit_response = client.post(
        f"/expenses/{expense_id}/submit",
        headers=auth_headers(employee_token),
    )

    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"

    register_user(client, "manager@test.com")
    change_role(
        db,
        "manager@test.com",
        UserRole.MANAGER,
    )
    manager_token = login_user(
        client,
        "manager@test.com",
    )

    approve_response = client.post(
        f"/expenses/{expense_id}/approve",
        headers=auth_headers(manager_token),
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    register_user(client, "accountant@test.com")
    change_role(
        db,
        "accountant@test.com",
        UserRole.ACCOUNTANT,
    )
    accountant_token = login_user(
        client,
        "accountant@test.com",
    )

    pay_response = client.post(
        f"/expenses/{expense_id}/pay",
        headers=auth_headers(accountant_token),
    )

    assert pay_response.status_code == 200
    assert pay_response.json()["status"] == "paid"

    audit_response = client.get(
        f"/expenses/{expense_id}/audit",
        headers=auth_headers(manager_token),
    )

    assert audit_response.status_code == 200

    actions = [
        item["action"]
        for item in audit_response.json()
    ]

    assert actions == [
        "created",
        "updated",
        "submitted",
        "approved",
        "paid",
    ]


def test_employee_cannot_approve_expense(client):
    register_user(client, "employee@test.com")
    token = login_user(client, "employee@test.com")

    response = create_expense(client, token)
    expense_id = response.json()["id"]

    client.post(
        f"/expenses/{expense_id}/submit",
        headers=auth_headers(token),
    )

    response = client.post(
        f"/expenses/{expense_id}/approve",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_submitted_expense_cannot_be_edited(client):
    register_user(client, "employee@test.com")
    token = login_user(client, "employee@test.com")

    response = create_expense(client, token)
    expense_id = response.json()["id"]

    client.post(
        f"/expenses/{expense_id}/submit",
        headers=auth_headers(token),
    )

    response = client.patch(
        f"/expenses/{expense_id}",
        headers=auth_headers(token),
        json={
            "amount": 999
        },
    )

    assert response.status_code == 409
