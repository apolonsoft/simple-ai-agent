# tests/test_item_service.py
from sqlalchemy.orm import Session
from app.services.item_service import ItemService
from app.schemas.item import ItemCreate


def test_service_create_and_fetch(db_session: Session):
    service = ItemService(db=db_session)

    # 1. Create item
    new_item_data = ItemCreate(title="Notebook", description="Dotted grid", price=12.0)
    created = service.create(new_item_data)

    assert created.id is not None
    assert created.title == "Notebook"

    # 2. Fetch item
    fetched = service.get_by_id(created.id)
    assert fetched is not None
    assert fetched.price == 12.0


def test_service_get_nonexistent_item_returns_none(db_session: Session):
    service = ItemService(db=db_session)
    result = service.get_by_id(999)
    assert result is None