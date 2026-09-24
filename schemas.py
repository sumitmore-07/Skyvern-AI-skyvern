from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["ok", "unverified", "failed"]


class PriceResult(BaseModel):
    """One product's price at one shop, as extracted by Skyvern."""

    product: str
    shop: str
    price: float | None = None
    currency: str | None = None
    in_stock: bool | None = None
    status: Status = "ok"
    note: str = ""


class ComparisonRow(BaseModel):
    """All shops' results for one product, with the cheapest available offer."""

    product: str
    results: list[PriceResult] = Field(default_factory=list)
    cheapest_shop: str | None = None
    cheapest_price: float | None = None
