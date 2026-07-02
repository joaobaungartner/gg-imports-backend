from decimal import Decimal

from src.entities.address import AddressEntity
from src.entities.admin import AdminEntity
from src.entities.cart import CartEntity
from src.entities.cart_item import CartItemEntity
from src.entities.category import CategoryEntity
from src.entities.client import ClientEntity
from src.entities.coupon import CouponEntity
from src.entities.order import OrderEntity
from src.entities.order_item import OrderItemEntity
from src.entities.payment import PaymentEntity
from src.entities.product import ProductEntity
from src.entities.user import UserEntity
from src.schemas.address_schema import AddressListResponse, AddressResponse
from src.schemas.admin_schema import AdminResponse
from src.schemas.cart_item_schema import (
    CartItemListResponse,
    CartItemResponse,
    CartItemSubtotalResponse,
)
from src.schemas.cart_schema import CartCheckoutResponse, CartResponse
from src.schemas.category_schema import CategoryListResponse, CategoryResponse
from src.schemas.client_schema import ClientResponse
from src.schemas.coupon_schema import CouponApplyResponse, CouponListResponse, CouponResponse
from src.schemas.order_item_schema import OrderItemListResponse, OrderItemResponse
from src.schemas.order_schema import OrderItemResponse as NestedOrderItemResponse
from src.schemas.order_schema import OrderListResponse, OrderResponse
from src.schemas.payment_schema import PaymentListResponse, PaymentResponse
from src.schemas.product_schema import (
    ProductAvailabilityResponse,
    ProductListResponse,
    ProductResponse,
)
from src.schemas.user_schema import UserResponse
from src.use_cases.cart.prepare_cart_checkout import CartCheckoutResult
from src.use_cases.coupon.apply_coupon import CouponApplyResult
from src.use_cases.product.check_product_availability import ProductAvailabilityResult


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def to_user_response(user: UserEntity) -> UserResponse:
    return UserResponse(
        id=user.id,
        nome=user.nome,
        email=user.email,
        telefone=user.telefone,
        data_cadastro=user.data_cadastro,
        role=_enum_value(user.role),
        ativo=user.ativo,
    )


def to_client_response(client: ClientEntity) -> ClientResponse:
    return ClientResponse(
        id=client.client_id,
        user_id=client.id,
        nome=client.nome,
        email=client.email,
        telefone=client.telefone,
        cpf=client.cpf,
        role=_enum_value(client.role),
        ativo=client.ativo,
        data_cadastro=client.data_cadastro,
    )


def to_admin_response(admin: AdminEntity) -> AdminResponse:
    return AdminResponse(
        id=admin.admin_id,
        user_id=admin.id,
        nome=admin.nome,
        email=admin.email,
        telefone=admin.telefone,
        role=_enum_value(admin.role),
        ativo=admin.ativo,
        data_cadastro=admin.data_cadastro,
    )


def to_category_response(category: CategoryEntity) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        nome=category.nome,
        descricao=category.descricao,
        ativo=category.ativo,
    )


def to_category_list_response(category: CategoryEntity) -> CategoryListResponse:
    return CategoryListResponse(
        id=category.id,
        nome=category.nome,
        descricao=category.descricao,
        ativo=category.ativo,
    )


def to_product_response(product: ProductEntity) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        category_id=product.category_id,
        nome=product.nome,
        descricao=product.descricao,
        preco=product.preco,
        tamanho=product.tamanho,
        clube=product.clube,
        tipo=product.tipo,
        estoque=product.estoque,
        imagem_url=product.imagem_url,
        ativo=product.ativo,
    )


def to_product_list_response(product: ProductEntity) -> ProductListResponse:
    return ProductListResponse(
        id=product.id,
        category_id=product.category_id,
        nome=product.nome,
        descricao=product.descricao,
        preco=product.preco,
        tamanho=product.tamanho,
        clube=product.clube,
        tipo=product.tipo,
        estoque=product.estoque,
        imagem_url=product.imagem_url,
        ativo=product.ativo,
    )


def to_cart_item_response(item: CartItemEntity) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        cart_id=item.cart_id,
        product_id=item.product_id,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        subtotal=item.subtotal(),
        ativo=item.ativo,
    )


def to_cart_item_list_response(item: CartItemEntity) -> CartItemListResponse:
    return CartItemListResponse(
        id=item.id,
        product_id=item.product_id,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        subtotal=item.subtotal(),
        ativo=item.ativo,
    )


def to_cart_response(cart: CartEntity) -> CartResponse:
    active_items = [item for item in cart.itens if item.ativo]
    return CartResponse(
        id=cart.id,
        client_id=cart.client_id,
        data_criacao=cart.data_criacao,
        ativo=cart.ativo,
        itens=[to_cart_item_response(item) for item in active_items],
        valor_total=cart.calcular_total(),
    )


def to_cart_checkout_response(result: CartCheckoutResult) -> CartCheckoutResponse:
    return CartCheckoutResponse(
        cart_id=result.cart_id,
        client_id=result.client_id,
        itens=[to_cart_item_response(item) for item in result.itens],
        valor_total=result.valor_total,
        valido_para_checkout=result.valido_para_checkout,
    )


def to_order_item_response(item: OrderItemEntity) -> OrderItemResponse:
    return OrderItemResponse(
        id=item.id,
        order_id=item.order_id,
        product_id=item.product_id,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        subtotal=item.subtotal(),
        ativo=item.ativo,
    )


def to_nested_order_item_response(item: OrderItemEntity) -> NestedOrderItemResponse:
    return NestedOrderItemResponse(
        id=item.id,
        product_id=item.product_id,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        subtotal=item.subtotal(),
        ativo=item.ativo,
    )


def to_order_item_list_response(item: OrderItemEntity) -> OrderItemListResponse:
    return OrderItemListResponse(
        id=item.id,
        product_id=item.product_id,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario,
        subtotal=item.subtotal(),
        ativo=item.ativo,
    )


def to_order_response(order: OrderEntity) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        client_id=order.client_id,
        endereco_id=order.endereco_id,
        pagamento_id=order.pagamento_id,
        cupom_id=order.cupom_id,
        data_pedido=order.data_pedido,
        valor_total=order.valor_total,
        status=_enum_value(order.status),
        ativo=order.ativo,
        itens=[to_nested_order_item_response(item) for item in order.itens if item.ativo],
    )


def to_order_list_response(order: OrderEntity) -> OrderListResponse:
    return OrderListResponse(
        id=order.id,
        client_id=order.client_id,
        data_pedido=order.data_pedido,
        valor_total=order.valor_total,
        status=_enum_value(order.status),
        ativo=order.ativo,
    )


def to_address_response(address: AddressEntity) -> AddressResponse:
    return AddressResponse(
        id=address.id,
        client_id=address.client_id,
        rua=address.rua,
        numero=address.numero,
        bairro=address.bairro,
        cidade=address.cidade,
        estado=address.estado,
        cep=address.cep,
        ativo=address.ativo,
    )


def to_address_list_response(address: AddressEntity) -> AddressListResponse:
    return AddressListResponse(
        id=address.id,
        rua=address.rua,
        numero=address.numero,
        bairro=address.bairro,
        cidade=address.cidade,
        estado=address.estado,
        cep=address.cep,
        ativo=address.ativo,
    )


def to_coupon_response(coupon: CouponEntity) -> CouponResponse:
    validade = coupon.validade
    if hasattr(validade, "date"):
        validade = validade.date()
    return CouponResponse(
        id=coupon.id,
        codigo=coupon.codigo,
        desconto=coupon.desconto,
        validade=validade,
        ativo=coupon.ativo,
    )


def to_coupon_list_response(coupon: CouponEntity) -> CouponListResponse:
    validade = coupon.validade
    if hasattr(validade, "date"):
        validade = validade.date()
    return CouponListResponse(
        id=coupon.id,
        codigo=coupon.codigo,
        desconto=coupon.desconto,
        validade=validade,
        ativo=coupon.ativo,
    )


def to_coupon_apply_response(result: CouponApplyResult) -> CouponApplyResponse:
    return CouponApplyResponse(
        coupon_id=result.coupon_id,
        codigo=result.codigo,
        valor_original=result.valor_original,
        desconto_aplicado=result.desconto_aplicado,
        valor_final=result.valor_final,
        valido=result.valido,
    )


def to_payment_response(payment: PaymentEntity) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        metodo=_enum_value(payment.metodo),
        status=_enum_value(payment.status),
        valor=payment.valor,
        codigo_transacao=payment.codigo_transacao,
        data_pagamento=payment.data_pagamento,
        ativo=payment.ativo,
    )


def to_payment_list_response(payment: PaymentEntity) -> PaymentListResponse:
    return PaymentListResponse(
        id=payment.id,
        order_id=payment.order_id,
        metodo=_enum_value(payment.metodo),
        status=_enum_value(payment.status),
        valor=payment.valor,
        data_pagamento=payment.data_pagamento,
        ativo=payment.ativo,
    )


def to_product_availability_response(
    result: ProductAvailabilityResult,
) -> ProductAvailabilityResponse:
    return ProductAvailabilityResponse(
        product_id=result.product_id,
        disponivel=result.disponivel,
        estoque_atual=result.estoque_atual,
        quantidade_solicitada=result.quantidade_solicitada,
    )


def to_cart_item_subtotal_response(
    item_id: int, subtotal: Decimal
) -> CartItemSubtotalResponse:
    return CartItemSubtotalResponse(id=item_id, subtotal=subtotal)
