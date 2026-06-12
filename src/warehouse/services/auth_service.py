"""Dịch vụ xác thực người dùng.

Tương ứng ``AuthService`` trong thiết kế: xử lý trực tiếp việc xác thực đăng
nhập, đăng ký tài khoản, đổi mật khẩu thông qua ``UserRepository`` và tiện ích
băm mật khẩu.
"""

from __future__ import annotations

from ..models.user import User, Role
from ..repositories.user_repository import UserRepository
from ..utils import security


class AuthError(Exception):
    """Ngoại lệ nghiệp vụ liên quan tới xác thực/đăng ký."""


class AuthService:
    """Xử lý nghiệp vụ xác thực và quản lý tài khoản ở mức thấp."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    def login(self, username: str, password: str) -> User:
        """Xác thực đăng nhập. Trả về ``User`` nếu thành công."""
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")

        user = self._users.find_by_username(username)
        if user is None or not security.verify_password(password, user.password_hash):
            raise AuthError("Tên đăng nhập hoặc mật khẩu không đúng.")
        return user

    def register(
        self,
        *,
        username: str,
        password: str,
        role: str = Role.STAFF,
        full_name: str = "",
        email: str = "",
        department: str = "",
        position: str = "",
        phone: str = "",
    ) -> User:
        """Đăng ký tài khoản mới."""
        username = (username or "").strip()
        if not username:
            raise AuthError("Tên đăng nhập không được để trống.")
        if len(password or "") < 4:
            raise AuthError("Mật khẩu phải có ít nhất 4 ký tự.")
        if role not in Role.ALL:
            raise AuthError("Vai trò không hợp lệ.")
        if self._users.exists(username):
            raise AuthError(f"Tên đăng nhập '{username}' đã tồn tại.")

        user = User(
            username=username,
            password_hash=security.hash_password(password),
            role=role,
            full_name=full_name.strip(),
            email=email.strip(),
            department=department.strip(),
            position=position.strip(),
            phone=phone.strip(),
        )
        user.id = self._users.insert(user)
        return user

    def change_password(self, username: str, old_password: str, new_password: str) -> None:
        """Đổi mật khẩu sau khi xác thực mật khẩu cũ."""
        user = self._users.find_by_username(username)
        if user is None:
            raise AuthError("Không tìm thấy tài khoản.")
        if not security.verify_password(old_password, user.password_hash):
            raise AuthError("Mật khẩu hiện tại không đúng.")
        if len(new_password or "") < 4:
            raise AuthError("Mật khẩu mới phải có ít nhất 4 ký tự.")
        self._users.update_password(username, security.hash_password(new_password))

    def update_profile(self, user: User) -> None:
        """Cập nhật hồ sơ cá nhân."""
        self._users.update_profile(user)
