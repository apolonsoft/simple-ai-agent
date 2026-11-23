# app/routes/auth_routes.py
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_controller import AuthController
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limiter import RateLimiter
from app.db.session import get_db
from app.models.user import UserModel
from app.schemas.user import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
    VerifyResetTokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(AuthService(db))


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RateLimiter(max_requests=10, window_seconds=60, scope="auth:register"))
    ],
)
async def register(
    user_in: UserCreate, controller: AuthController = Depends(get_auth_controller)
):
    return await controller.register(user_in)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[
        Depends(RateLimiter(max_requests=10, window_seconds=60, scope="auth:login"))
    ],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    controller: AuthController = Depends(get_auth_controller),
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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            RateLimiter(
                max_requests=5, window_seconds=900, scope="auth:forgot-password"
            )
        )
    ],
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    controller: AuthController = Depends(get_auth_controller),
):
    """Initiates password reset flow and dispatches email via SMTP/Mailpit."""
    return await controller.forgot_password(
        email=request_data.email, background_tasks=background_tasks
    )


@router.get(
    "/verify-reset-token",
    response_model=VerifyResetTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_reset_token(
    token: str = Query(..., description="Password reset token from email link"),
    controller: AuthController = Depends(get_auth_controller),
):
    """Verifies validity and unexpired state of a reset token before form submission."""
    return await controller.verify_reset_token(token=token)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    """Consumes the reset token and updates the user's password."""
    return await controller.reset_password(
        token=reset_data.token, new_password=reset_data.new_password
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            RateLimiter(max_requests=5, window_seconds=60, scope="auth:change-password")
        )
    ],
)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
) -> MessageResponse:
    """Protected endpoint: Updates password for authenticated user and revokes concurrent sessions."""
    return await controller.change_password(
        user=current_user, request_data=request_data
    )
