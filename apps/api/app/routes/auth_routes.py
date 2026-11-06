# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.controllers.auth_controller import AuthController
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.dependencies import get_current_user, require_role
from app.models.user import UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(AuthService(db))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    controller: AuthController = Depends(get_auth_controller)
):
    return await controller.register(user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    controller: AuthController = Depends(get_auth_controller)
):
    return await controller.login(email=form_data.username, password=form_data.password)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """Protected endpoint: Returns the currently authenticated user."""
    return current_user


@router.get("/admin-only")
async def admin_dashboard(admin_user: UserModel = Depends(require_role("admin"))):
    """Protected endpoint: Only users with role 'admin' can access."""
    return {"message": f"Welcome Admin {admin_user.email}"}
