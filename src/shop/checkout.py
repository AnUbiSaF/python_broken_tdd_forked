"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _validate_line(order_line: dict[str, str]) -> str | None:
    missing_key = next((key for key in REQUIRED_LINE_KEYS if key not in order_line), None)
    if missing_key is not None:
        return f"missing required key: {missing_key}"
    if order_line["sku"] == "":
        return "sku must not be empty"
    quantity_text = order_line["qty"].strip().lstrip("+-")
    if not quantity_text.isdigit():
        return "quantity must be an integer"
    if int(order_line["qty"]) <= 0:
        return "quantity must be greater than zero"
    price_text = order_line["unit_price_kopecks"].strip().lstrip("+-")
    if not price_text.isdigit():
        return "price must be an integer"
    if int(order_line["unit_price_kopecks"]) < 0:
        return "price must not be negative"
    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "order must contain at least one line"
    seen_skus: set[str] = set()
    for order_line in lines:
        line_error = _validate_line(order_line)
        if line_error is not None:
            return line_error
        if order_line["sku"] in seen_skus:
            return "sku must be unique"
        seen_skus.add(order_line["sku"])
    if promo_code and promo_code not in PROMO_CODES:
        return "unknown promo code"
    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "unsupported shipping city"
    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None
    subtotal = sum(
        int(order_line["qty"]) * int(order_line["unit_price_kopecks"]) for order_line in lines
    )
    total_quantity = sum(int(order_line["qty"]) for order_line in lines)
    tier_discount = max(
        (discount for threshold, discount in TIER_DISCOUNTS if total_quantity >= threshold),
        default=0,
    )
    promo_discount = PROMO_CODES.get(promo_code, 0)
    discount_percent = min(max(tier_discount, promo_discount), MAX_DISCOUNT_PERCENT)
    discounted_subtotal = subtotal - percent_of(subtotal, discount_percent)
    delivery = (
        SHIPPING_KOPEKS if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS else 0
    )
    base = discounted_subtotal + delivery
    return base + percent_of(base, VAT_PERCENT)
