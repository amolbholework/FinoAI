from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_effective_user
from app.models.category import Category, owned_or_system
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return (
        db.query(Category)
        .filter(owned_or_system(current_user.id))
        .order_by(Category.is_system.desc(), Category.name)
        .all()
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    existing = (
        db.query(Category)
        .filter(Category.name == payload.name, owned_or_system(current_user.id))
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A category with that name already exists.")

    category = Category(user_id=current_user.id, name=payload.name, is_system=False)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    category = (
        db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    )
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found.")
    if category.is_system:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "System categories can't be deleted.")
    db.delete(category)
    db.commit()
