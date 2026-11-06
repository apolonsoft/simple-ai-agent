# tests/test_item_api.py
from fastapi import status
from fastapi.testclient import TestClient

def test_create_item_success(client: TestClient):
    # Arrange
    payload = {
        "title": "Mechanical Keyboard",
        "description": "Clicky tactile switches",
        "price": 99.99
    }

    # Act
    response = client.post("/api/v1/items/", json=payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == payload["title"]
    assert data["price"] == payload["price"]


def test_create_item_invalid_price(client: TestClient):
    """Pydantic validation should block negative or zero prices."""
    payload = {
        "title": "Invalid Item",
        "price": -10.0  # Invalid per Field(..., gt=0)
    }

    response = client.post("/api/v1/items/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_item_by_id_found(client: TestClient):
    # Arrange: Create an item first
    create_res = client.post("/api/v1/items/", json={"title": "Mouse", "price": 49.50})
    item_id = create_res.json()["id"]

    # Act
    response = client.get(f"/api/v1/items/{item_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Mouse"


def test_get_item_by_id_not_found(client: TestClient):
    # Act: Query an ID that does not exist
    response = client.get("/api/v1/items/9999")

    # Assert: Should trigger 404 from the ItemController
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Item with id 9999 not found."