from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity, UserRole
from src.repositories.address_repository import AddressRepository
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.user_repository import UserRepository
from src.utils.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserEntity:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou inválido",
        )

    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou inválido",
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou inválido",
        ) from exc

    user = UserRepository(db).get_by_id(user_id_int)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return user


def get_current_admin(
    current_user: UserEntity = Depends(get_current_user),
) -> UserEntity:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada",
        )
    return current_user


def get_current_client(
    current_user: UserEntity = Depends(get_current_user),
) -> UserEntity:
    if current_user.role != UserRole.CLIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada",
        )
    return current_user


def require_same_user_or_admin(
    target_user_id: int, current_user: UserEntity
) -> None:
    if current_user.is_admin():
        return
    if current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada",
        )


def require_admin_or_self(user_id: int, current_user: UserEntity) -> None:
    require_same_user_or_admin(user_id, current_user)


def ensure_client_owner_or_admin(
    client_id: int, current_user: UserEntity, db: Session
) -> None:
    if current_user.is_admin():
        return

    client = ClientRepository(db).get_by_id(client_id)
    if not client or client.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada",
        )


def ensure_client_access_by_user_id(
    user_id: int, current_user: UserEntity
) -> None:
    require_same_user_or_admin(user_id, current_user)


def ensure_client_access_by_cpf(
    cpf: str, current_user: UserEntity, db: Session
) -> None:
    if current_user.is_admin():
        return

    client = ClientRepository(db).get_by_cpf(cpf)
    if not client or client.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada",
        )


def ensure_cart_owner_or_admin(
    cart_id: int, current_user: UserEntity, db: Session
) -> None:
    cart = CartRepository(db).get_by_id(cart_id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrinho não encontrado",
        )
    ensure_client_owner_or_admin(cart.client_id, current_user, db)


def ensure_cart_item_owner_or_admin(
    cart_item_id: int, current_user: UserEntity, db: Session
) -> None:
    item = CartItemRepository(db).get_by_id(cart_item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item do carrinho não encontrado",
        )
    ensure_cart_owner_or_admin(item.cart_id, current_user, db)


def ensure_order_owner_or_admin(
    order_id: int, current_user: UserEntity, db: Session
) -> None:
    order = OrderRepository(db).get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado",
        )
    ensure_client_owner_or_admin(order.client_id, current_user, db)


def ensure_order_item_owner_or_admin(
    order_item_id: int, current_user: UserEntity, db: Session
) -> None:
    item = OrderItemRepository(db).get_by_id(order_item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item do pedido não encontrado",
        )
    ensure_order_owner_or_admin(item.order_id, current_user, db)


def ensure_address_owner_or_admin(
    address_id: int, current_user: UserEntity, db: Session
) -> None:
    address = AddressRepository(db).get_by_id(address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endereço não encontrado",
        )
    ensure_client_owner_or_admin(address.client_id, current_user, db)


def ensure_payment_owner_or_admin(
    payment_id: int, current_user: UserEntity, db: Session
) -> None:
    payment = PaymentRepository(db).get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado",
        )
    ensure_order_owner_or_admin(payment.order_id, current_user, db)


def ensure_payment_access_by_order(
    order_id: int, current_user: UserEntity, db: Session
) -> None:
    ensure_order_owner_or_admin(order_id, current_user, db)
