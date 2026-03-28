from __future__ import annotations

from .base import ActionSpec, BlogPostSpec, EmailDocument, MenuItemSpec, MetricSpec, PricingPlanSpec, ProductSpec, SocialLinkSpec
from .sections import (
    BlogList,
    CallToAction,
    Coupon,
    Footer,
    Header,
    Hero,
    OrderSummary,
    Pricing,
    ProductDetail,
    ProductFeatures,
    ProductList,
    Stats,
)


class MarketingTemplate(EmailDocument):
    def __init__(self, *, brand: str, hero_title: str, hero_body: str, cta_label: str, cta_href: str = "#", **kwargs: object) -> None:
        super().__init__(
            sections=[
                Header(brand, [MenuItemSpec("Features", href="#features"), MenuItemSpec("Pricing", href="#pricing")], **kwargs),
                Hero(
                    eyebrow="New launch",
                    title=hero_title,
                    body=hero_body,
                    primary_action=ActionSpec(cta_label, href=cta_href, variant="primary"),
                    secondary_action=ActionSpec("View gallery", href="#gallery", variant="secondary"),
                    meta_items=[
                        MetricSpec(label="Higher click-through", value="42%", detail="Across recent launch sends"),
                        MetricSpec(label="Preset personalities", value="5", detail="Ready for different campaign moods"),
                        MetricSpec(label="From idea to send", value="<1h", detail="With reusable sections"),
                    ],
                    **kwargs,
                ),
                Stats(
                    [
                        MetricSpec(label="Open rate", value="58%", detail="Across recent launch sends"),
                        MetricSpec(label="CTR", value="9.1%", detail="Driven by richer CTAs"),
                        MetricSpec(label="Replies", value="214", detail="From customers and prospects"),
                    ],
                    **kwargs,
                ),
                CallToAction(
                    "Ready to start?",
                    "Compose from reusable sections, stronger defaults, and richer visual hierarchy.",
                    [
                        ActionSpec(cta_label, href=cta_href, variant="primary"),
                        ActionSpec("Browse components", href="#components", variant="ghost"),
                    ],
                    **kwargs,
                ),
                Footer(brand, [SocialLinkSpec(label="Twitter", href="#"), SocialLinkSpec(label="LinkedIn", href="#")], **kwargs),
            ],
            preview_text=hero_body,
            title=hero_title,
            **kwargs,
        )


class NewsletterTemplate(EmailDocument):
    def __init__(self, *, brand: str, posts: list[BlogPostSpec], **kwargs: object) -> None:
        super().__init__(
            sections=[
                Header(brand, **kwargs),
                CallToAction(
                    "Weekly editorial dispatch",
                    "Long-form product notes, changelog context, and examples worth borrowing.",
                    [ActionSpec("Read the latest issue", href="#", variant="primary")],
                    **kwargs,
                ),
                BlogList(posts, **kwargs),
                Footer(brand, [SocialLinkSpec(label="X", href="#"), SocialLinkSpec(label="GitHub", href="#")], **kwargs),
            ],
            preview_text="Latest stories",
            title=f"{brand} newsletter",
            **kwargs,
        )


class PromoTemplate(EmailDocument):
    def __init__(self, *, brand: str, code: str, detail: str, plans: list[PricingPlanSpec], **kwargs: object) -> None:
        super().__init__(
            sections=[
                Header(brand, **kwargs),
                Coupon(code, detail, **kwargs),
                Pricing(plans, **kwargs),
                CallToAction("Offer ends soon", "Use the code above before the Friday close.", [ActionSpec("Redeem offer", href="#", variant="primary")], **kwargs),
                Footer(brand, **kwargs),
            ],
            preview_text=detail,
            title=f"{brand} offer",
            **kwargs,
        )


class ProductAnnouncementTemplate(EmailDocument):
    def __init__(self, *, brand: str, product: ProductSpec, related: list[ProductSpec], **kwargs: object) -> None:
        sections = [
            Header(brand, **kwargs),
            ProductDetail(
                product.name,
                product.price,
                product.description,
                product.image_src,
                action=product.action or ActionSpec(product.label, href=product.href, variant="primary"),
                **kwargs,
            ),
        ]
        if product.features:
            sections.append(ProductFeatures(product.features, **kwargs))
        if related:
            sections.append(ProductList(related, **kwargs))
        sections.append(Footer(brand, **kwargs))
        super().__init__(
            sections=sections,
            preview_text=product.description,
            title=product.name,
            **kwargs,
        )


class OrderTemplate(EmailDocument):
    def __init__(self, *, brand: str, summary_rows: list[tuple[str, str]], **kwargs: object) -> None:
        super().__init__(
            sections=[
                Header(brand, **kwargs),
                CallToAction(
                    "Your order is moving",
                    "Track fulfillment, confirm totals, and keep customers confident without leaving the email.",
                    [ActionSpec("Track package", href="#", variant="primary")],
                    **kwargs,
                ),
                OrderSummary(summary_rows, progress=75, **kwargs),
                Footer(brand, **kwargs),
            ],
            preview_text="Your order update",
            title="Order summary",
            **kwargs,
        )
