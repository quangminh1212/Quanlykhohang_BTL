"""Dịch vụ quản lý tài khoản (lớp nghiệp vụ trung gian).

Tương ứng ``AccountService`` trong thiết kế: cung cấp giao diện nghiệp vụ cho
tầng UI, ủy quyền các thao tác xác thực cho ``AuthService``.
"""

from __future__ import annotations

from ..models.user import User
from ..repositories.user_repository import UserRepository
from .auth_service import AuthService


class AccountService:
    """Lớp trung gian cung cấp nghiệp vụ tài khoản cho tầng giao diện."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository
        self._auth = AuthService(user_repository)

    def login(self, username: str, password: str) -> User:
        return self._auth.login(username, password)

    def register(self, **kwargs) -> User:
        return self._auth.register(**kwargs)

    def change_password(self, username: str, old_password: str, new_password: str) -> None:
        self._auth.change_password(username, old_password, new_password)

    def update_profile(self, user: User) -> None:
        self._auth.update_profile(user)

    def find_all_users(self) -> list[User]:
        return self._users.find_all()
