from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)

    def register(self, data: UserCreate) -> User:
        email = str(data.email).strip().lower()

        existing_user = self.user_repository.get_by_email(email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            email=email,
            password_hash=hash_password(data.password.get_secret_value()),
        )

        try:
            self.user_repository.add(user)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()

            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            )

            if constraint_name == "uq_users_email":
                raise EmailAlreadyRegisteredError from exc

            raise

        self.db.refresh(user)
        return user

    def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> User:
        normalized_email = email.strip().lower()

        user = self.user_repository.get_by_email(normalized_email)

        if user is None:
            raise InvalidCredentialsError

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InvalidCredentialsError

        return user
