from __future__ import annotations

import inspect
import json
import re
import shutil
import sys
from hashlib import sha1
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from textwrap import dedent
from typing import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pyzahidal as ui
from pyzahidal.rendering import render_tag


ALIASES = {
    "Content": "Section",
    "Grid": "Row",
    "Logos": "LogoCloud",
    "Navigation": "Nav",
    "Spacing": "Spacer",
}

SKIPPED_EXPORTS = {
    "ActionSpec",
    "AvatarSpec",
    "BentoItemSpec",
    "BlogPostSpec",
    "CartItemSpec",
    "Component",
    "ComponentSpec",
    "DataColumnSpec",
    "DEFAULT_THEME",
    "Raw",
    "Renderable",
    "FaqItemSpec",
    "HeroMediaSpec",
    "ImageSpec",
    "JinjaExpr",
    "LogoSpec",
    "MenuItemSpec",
    "MetricSpec",
    "PricingPlanSpec",
    "ProductSpec",
    "ReviewSpec",
    "SocialLinkSpec",
    "TeamMemberSpec",
    "TestimonialSpec",
    "THEMES",
    "TimelineStepSpec",
    "build_theme",
    "jinja",
    "raw",
    *ALIASES.keys(),
}

GROUPS = {
    "EmailDocument": "document",
    "Alert": "primitives",
    "Avatar": "primitives",
    "AvatarGroup": "primitives",
    "Button": "primitives",
    "Column": "primitives",
    "Columns": "primitives",
    "Container": "primitives",
    "DataTable": "primitives",
    "Divider": "primitives",
    "Heading": "primitives",
    "IconLink": "primitives",
    "Image": "primitives",
    "ImageGroup": "primitives",
    "Inline": "primitives",
    "Link": "primitives",
    "LogoStrip": "primitives",
    "Menu": "primitives",
    "Metric": "primitives",
    "Nav": "primitives",
    "Pill": "primitives",
    "ProgressBar": "primitives",
    "Row": "primitives",
    "Section": "primitives",
    "Stack": "primitives",
    "Surface": "primitives",
    "SocialLinks": "primitives",
    "Spacer": "primitives",
    "Text": "primitives",
    "BentoGrid": "sections",
    "BlogList": "sections",
    "CallToAction": "sections",
    "CategoryPreview": "sections",
    "Coupon": "sections",
    "FAQ": "sections",
    "Feature": "sections",
    "Footer": "sections",
    "Header": "sections",
    "Hero": "sections",
    "LogoCloud": "sections",
    "OrderSummary": "sections",
    "Pricing": "sections",
    "ProductDetail": "sections",
    "ProductFeatures": "sections",
    "ProductList": "sections",
    "Reviews": "sections",
    "ShoppingCart": "sections",
    "Stats": "sections",
    "Team": "sections",
    "Testimonials": "sections",
    "Timeline": "sections",
    "WelcomeHero": "sections",
    "MarketingTemplate": "templates",
    "NewsletterTemplate": "templates",
    "OrderTemplate": "templates",
    "ProductAnnouncementTemplate": "templates",
    "PromoTemplate": "templates",
}

GROUP_TITLES = {
    "document": "Document Shell",
    "primitives": "Primitives",
    "sections": "Sections",
    "templates": "Templates",
}

DESCRIPTION_BY_NAME = {
    "EmailDocument": "Wraps sections in the final email shell with preview text, title, and theme control.",
    "Alert": "Highlights short content blocks with a tone-aware background.",
    "Avatar": "Renders a circular image for people, authors, or customer references.",
    "AvatarGroup": "Stacks avatars with overlap for team, social proof, or welcome states.",
    "Button": "Creates a call-to-action link styled as a button.",
    "Column": "Provides inline column layout inside a row.",
    "Columns": "Builds email-safe table columns with explicit widths or equal distribution.",
    "Container": "Creates a themed surface wrapper using an email-safe table.",
    "DataTable": "Renders labeled tabular data with theme-aware borders and typography.",
    "Divider": "Adds a horizontal divider line between content blocks.",
    "Heading": "Renders a themed heading with stronger visual hierarchy.",
    "IconLink": "Renders an icon-first link tile for social or utility actions.",
    "Image": "Displays a responsive image with themed rounding.",
    "ImageGroup": "Composes linked or captioned images into grid or masonry-style layouts.",
    "Inline": "Places child items inline with consistent spacing.",
    "Link": "Renders a theme-aware text link without button chrome.",
    "LogoStrip": "Arranges text or image logos with optional boxed treatments.",
    "Menu": "Builds horizontal or vertical navigation from link items.",
    "Metric": "Displays a stat value with optional label, detail, and trend chip.",
    "Nav": "Low-level wrapper for custom navigation markup.",
    "Pill": "Displays a compact rounded label for status or category tags.",
    "ProgressBar": "Shows percentage progress using a themed track and fill.",
    "Row": "Builds an email-safe table row from column content.",
    "Section": "Applies content padding around child blocks inside a table section.",
    "Stack": "Stacks child items vertically with consistent spacing or dividers.",
    "Surface": "Creates a token-driven card or panel with optional background image, including overlay treatments on top of photography.",
    "SocialLinks": "Renders a horizontal list of text links for social or utility destinations.",
    "Spacer": "Adds fixed vertical whitespace between elements.",
    "Text": "Renders body copy with the active theme's text styles.",
    "BentoGrid": "Stacks highlighted content cards for feature or campaign summaries.",
    "BlogList": "Formats a list of posts with title, excerpt, and link action.",
    "CallToAction": "Presents a highlighted conversion block with one or more actions.",
    "CategoryPreview": "Shows a titled list of category links as pill-like buttons.",
    "Coupon": "Displays a promotion code and supporting detail.",
    "FAQ": "Stacks question and answer pairs in a readable layout.",
    "Feature": "Renders a single feature spotlight with icon, title, and body.",
    "Footer": "Provides company, social links, and opt-in reminder content.",
    "Header": "Displays a brand label with optional navigation links.",
    "Hero": "Creates the main above-the-fold message area with actions, media, and supporting proof points.",
    "LogoCloud": "Displays partner or customer logos as text or images.",
    "OrderSummary": "Summarizes order rows and optional fulfillment progress.",
    "Pricing": "Shows one or more pricing plans with featured-state emphasis and feature lists.",
    "ProductDetail": "Focuses on a single product with optional image and pricing.",
    "ProductFeatures": "Lists product selling points as bullet-style copy.",
    "ProductList": "Displays multiple product summaries with price and CTA.",
    "Reviews": "Alias-like wrapper around testimonial-style review entries.",
    "ShoppingCart": "Shows cart rows using a table with item, quantity, and price.",
    "Stats": "Displays quick summary metrics in compact columns with supporting detail.",
    "Team": "Shows a list of team members with avatar, name, and role.",
    "Testimonials": "Stacks quote cards with author attribution.",
    "Timeline": "Displays changelog entries with version, date, category, and detail.",
    "WelcomeHero": "Creates a centered onboarding-style welcome block with team avatars and a single CTA.",
    "MarketingTemplate": "Starter email for launches or general product marketing.",
    "NewsletterTemplate": "Starter email for editorial or blog roundups.",
    "OrderTemplate": "Starter email for order status and summary content.",
    "ProductAnnouncementTemplate": "Starter email for product launches and related items.",
    "PromoTemplate": "Starter email for promotional code and pricing offers.",
}

SPECIAL_NOTES = {
    "Alert": ["`tone` supports `info`, `success`, `warning`, and `danger`."],
    "Column": ["Use `width` to control the column share inside a `Row`."],
    "Columns": ["Pass `widths` to control uneven layouts without wrapping each child in `Column`."],
    "DataTable": ["`rows` accepts any renderable or plain value per cell."],
    "EmailDocument": ["`theme` can be a preset name or a token dictionary.", "`theme_overrides` wins over the base preset."],
    "Feature": ["`icon` defaults to a bullet when not provided."],
    "AvatarGroup": ["Use `overlap` to control how tightly avatars stack together."],
    "IconLink": ["Use `shape='circle'` for social tiles or `shape='rounded'` for boxed icon buttons."],
    "ImageGroup": ["Set `masonry=True` to distribute image tiles by column instead of rows."],
    "Menu": ["`orientation='vertical'` renders links through `Stack`."],
    "Metric": ["Use `trend` for positive or negative deltas like `+25%` or `-3%`."],
    "Hero": ["Use `primary_action` and optional `secondary_action` dictionaries to control CTA treatments."],
    "Nav": ["`Nav` is intentionally low-level; `Header` is the higher-level entrypoint most users want."],
    "OrderSummary": ["`progress=None` omits the progress bar."],
    "ProgressBar": ["The fill width is clamped between 0 and 100 percent."],
    "Reviews": ["`Reviews` renders through `Testimonials` with the same input shape."],
    "Section": ["`Section` automatically applies themed content padding to its cell."],
    "Stack": ["Set `divider=True` to insert themed rules between items."],
    "Spacer": ["Use email-safe pixel strings such as `8px` or `24px`."],
    "Surface": ["Use `background_image` for email-safe hero, CTA, or banner panels without dropping to raw HTML.", "`tone='overlay'` creates a translucent content panel on top of image-backed surfaces."],
}

THEME_DESCRIPTIONS = {
    "default": "Neutral baseline palette for product and transactional layouts.",
    "editorial": "Warmer serif-led presentation for newsletter and long-form content.",
    "vibrant": "Higher-energy warm palette for promotional campaigns.",
    "modern": "Cooler blue-forward palette with softer rounded geometry.",
    "commerce": "Amber retail palette aimed at catalog and conversion emails.",
}

CURATED_EXPORT = ROOT / "curated_components_export.json"
CURATED_CATEGORY_THEME = {
    "HERO": "modern",
    "Call to Action": "modern",
    "Feature": "modern",
    "Bento grids": "modern",
    "Images": "editorial",
    "Blog": "editorial",
    "Content": "editorial",
    "Team": "editorial",
    "Testimonials": "editorial",
    "Reviews": "editorial",
    "Pricing": "commerce",
    "Product Lists": "commerce",
    "Product Detail": "commerce",
    "Product Features": "commerce",
    "Category Previews": "commerce",
    "Shopping Cart": "commerce",
    "Order Summary": "commerce",
    "Coupons": "vibrant",
    "Stats": "vibrant",
    "Logos": "default",
    "Headers": "default",
    "Footers": "default",
    "Social": "default",
    "FAQs": "default",
    "Timelines": "default",
    "Containers": "default",
    "Grids": "default",
    "Spacing": "default",
    "Buttons": "default",
    "Pills": "default",
    "Avatars": "default",
    "Alerts": "default",
    "Navigation": "default",
    "Progress Bars": "default",
    "Data Tables": "default",
}

EXAMPLE_TRACKS = [
    (
        "Product announcement",
        "Launch-oriented examples for product reveals, feature highlights, and announcement-style hero layouts.",
        {"HERO", "Feature", "Bento grids", "Headers", "Footers", "Logos"},
    ),
    (
        "Newsletter and editorial",
        "Examples for recurring editorial sends, content digests, community updates, and people-focused sections.",
        {"Blog", "Content", "FAQs", "Team", "Testimonials", "Timelines"},
    ),
    (
        "Promotion and campaigns",
        "Examples for campaigns that center urgency, conversion, and high-visibility calls to action.",
        {"Coupons", "Call to Action", "Stats", "Pricing"},
    ),
    (
        "Ecommerce and order flows",
        "Examples for catalog, purchase, cart, review, and order-summary experiences.",
        {"Product Lists", "Product Detail", "Category Previews", "Shopping Cart", "Reviews", "Order Summary"},
    ),
    (
        "Utility and layout patterns",
        "Lower-level patterns that help you compose custom emails when starter templates are not enough.",
        {"Images", "Social", "Containers", "Grids", "Spacing", "Buttons", "Pills", "Avatars", "Progress Bars", "Data Tables"},
    ),
]


@dataclass(frozen=True)
class CuratedExampleSpec:
    category: str
    title: str
    slug: str
    description: str
    code: str
    factory: Callable[[], object]
    theme: str
    screenshot_path: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def curated_theme(category: str) -> str:
    return CURATED_CATEGORY_THEME.get(category, "default")


def example_track_for_category(category: str) -> tuple[str, str]:
    for title, description, categories in EXAMPLE_TRACKS:
        if category in categories:
            return title, description
    return "More patterns", "Additional curated examples that do not fit one of the primary tracks yet."


def load_curated_source_map() -> dict[tuple[str, str], str]:
    if not CURATED_EXPORT.exists():
        return {}
    payload = json.loads(CURATED_EXPORT.read_text(encoding="utf-8"))
    source_map: dict[tuple[str, str], str] = {}
    for page in payload.get("pages", []):
        category = page["pageHeading"]
        for section in page.get("sections", []):
            title = section.get("previewHeading") or section.get("heading") or section["slug"]
            source_map.setdefault((category, title.replace(" Preview", "").strip()), page["pageUrl"])
    return source_map


def svg_data_url(label: str, width: int = 640, height: int = 320, bg: str = "#dbeafe", fg: str = "#1d4ed8") -> str:
    safe_label = label.replace("&", "&amp;")
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        f"<rect width='100%' height='100%' fill='{bg}'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"font-family='Arial, Helvetica, sans-serif' font-size='32' fill='{fg}'>{safe_label}</text>"
        "</svg>"
    )
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def code_string_literal(value: str) -> str:
    return json.dumps(value)


def branded_logo_data_url(label: str, width: int, bg: str = "#f8fafc", fg: str = "#0f172a") -> str:
    safe_label = label.replace("&", "&amp;")
    height = 44
    font_size = max(16, min(26, width // 3))
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        f"<rect width='100%' height='100%' rx='12' fill='{bg}'/>"
        f"<text x='50%' y='52%' dominant-baseline='middle' text-anchor='middle' "
        f"font-family='Arial, Helvetica, sans-serif' font-size='{font_size}' font-weight='700' fill='{fg}'>{safe_label}</text>"
        "</svg>"
    )
    return f"data:image/svg+xml;utf8,{quote(svg)}"


def curated_logo_markup(label: str, width: int, bg: str = "#f8fafc", fg: str = "#0f172a") -> ui.Renderable:
    src = branded_logo_data_url(label, width, bg=bg, fg=fg)
    return ui.raw(
        render_tag(
            "img",
            attrs={"src": src, "alt": label},
            styles={"display": "block", "width": f"{width}px", "height": "auto"},
        )
    )


def _action_spec(label: str, href: str = "#", variant: str = "primary") -> ui.ActionSpec:
    return ui.ActionSpec(label, href=href, variant=variant)


def _avatar_spec(src: str, alt: str = "", *, name: str = "") -> ui.AvatarSpec:
    return ui.AvatarSpec(src, alt=alt, name=name)


def _image_spec(src: str, alt: str = "") -> ui.ImageSpec:
    return ui.ImageSpec(src, alt=alt)


def _menu_item_spec(label: str, href: str = "#") -> ui.MenuItemSpec:
    return ui.MenuItemSpec(label, href=href)


def _social_link_spec(href: str = "#", *, label: str = "", icon_src: str = "", alt: str = "") -> ui.SocialLinkSpec:
    return ui.SocialLinkSpec(href=href, label=label, icon_src=icon_src, alt=alt)


def _logo_spec(label: str, src: str = "") -> ui.LogoSpec:
    return ui.LogoSpec(label, src=src)


def _metric_spec(label: object, value: object, detail: object | None = None, trend: str | None = None) -> ui.MetricSpec:
    return ui.MetricSpec(label=label, value=value, detail=detail, trend=trend)


def _faq_spec(question: str, answer: str) -> ui.FaqItemSpec:
    return ui.FaqItemSpec(question, answer)


def _timeline_step_spec(version: str, date: str, category: str, title: str, detail: str) -> ui.TimelineStepSpec:
    return ui.TimelineStepSpec(version, date, category, title, detail)


def _curated_plain_icon_link(item: object, *, theme: str, size: str = "20px") -> object:
    href = str(getattr(item, "href", item.get("href", "#") if isinstance(item, dict) else "#"))
    label = str(getattr(item, "label", item.get("label", "") if isinstance(item, dict) else ""))
    alt = str(getattr(item, "alt", item.get("alt", label) if isinstance(item, dict) else label))
    src = str(getattr(item, "icon_src", item.get("icon_src", item.get("src", "")) if isinstance(item, dict) else ""))
    image = render_tag(
        "img",
        attrs={"src": src, "alt": alt},
        styles={"display": "block", "width": size, "height": size, "margin": "0 auto"},
    )
    return ui.Link(
        ui.raw(image),
        href=href,
        theme=theme,
        styles={"display": "inline-block", "line-height": "1"},
    )


def _curated_plain_icon_row(items: list[object], *, theme: str, align: str = "center", gap: str = "24px") -> object:
    return ui.Inline(
        *[_curated_plain_icon_link(item, theme=theme) for item in items],
        align=align,
        gap=gap,
        wrap=True,
        theme=theme,
    )


def _curated_stacked_social_link(item: object, *, theme: str) -> object:
    label = str(getattr(item, "label", item.get("label") if isinstance(item, dict) else "") or getattr(item, "alt", item.get("alt", "") if isinstance(item, dict) else "") or "Social")
    href = str(getattr(item, "href", item.get("href", "#") if isinstance(item, dict) else "#"))
    src = str(getattr(item, "icon_src", item.get("icon_src", item.get("src", "")) if isinstance(item, dict) else ""))
    inner = render_tag(
        "span",
        styles={"display": "inline-block", "text-align": "center"},
        children=[
            render_tag(
                "span",
                styles={
                    "display": "block",
                    "width": "40px",
                    "height": "40px",
                    "margin": "0 auto",
                    "border-radius": "999px",
                    "background": "#eef4ff",
                    "border": "1px solid #d5deeb",
                },
                children=[
                    ui.raw(
                        render_tag(
                            "img",
                            attrs={"src": src, "alt": label},
                            styles={"display": "block", "width": "20px", "height": "20px", "margin": "9px auto 0"},
                        )
                    )
                ],
            ),
            ui.raw(render_tag("span", styles={"display": "block", "height": "8px", "line-height": "8px", "font-size": "8px"}, children=[""])),
            render_tag("span", styles={"display": "block"}, children=[label]),
        ],
    )
    return ui.Link(
        ui.raw(inner),
        href=href,
        theme=theme,
        styles={
            "display": "inline-block",
            "text-align": "center",
            "min-width": "86px",
            "padding": "14px 12px 12px",
            "border-radius": "18px",
            "border": "1px solid #d5deeb",
            "background": "#ffffff",
            "box-shadow": "0 10px 24px rgba(15, 23, 42, 0.08)",
            "font-size": "13px",
            "font-weight": "600",
            "line-height": "1.25",
            "color": "#334155",
        },
    )


def _curated_stacked_social_row(items: list[object], *, theme: str) -> object:
    return ui.Inline(
        *[_curated_stacked_social_link(item, theme=theme) for item in items],
        align="center",
        gap="18px",
        wrap=True,
        theme=theme,
    )


def _curated_chip_icon_link(item: object, *, theme: str, size: str = "18px") -> object:
    href = str(getattr(item, "href", item.get("href", "#") if isinstance(item, dict) else "#"))
    label = str(getattr(item, "label", item.get("label", "") if isinstance(item, dict) else ""))
    alt = str(getattr(item, "alt", item.get("alt", label) if isinstance(item, dict) else label))
    src = str(getattr(item, "icon_src", item.get("icon_src", item.get("src", "")) if isinstance(item, dict) else ""))
    image = render_tag(
        "img",
        attrs={"src": src, "alt": alt},
        styles={"display": "block", "width": size, "height": size, "margin": "0 auto"},
    )
    return ui.Link(
        ui.raw(image),
        href=href,
        theme=theme,
        styles={
            "display": "inline-block",
            "width": "36px",
            "height": "36px",
            "line-height": "36px",
            "text-align": "center",
            "border-radius": "999px",
            "border": "1px solid #e7d9ca",
            "background": "#fff7f0",
            "box-shadow": "0 6px 14px rgba(67, 54, 43, 0.08)",
        },
    )


def _curated_team_social_row(items: list[object], *, theme: str) -> object:
    return ui.Inline(
        *[_curated_chip_icon_link(item, theme=theme) for item in items],
        align="center",
        gap="10px",
        wrap=True,
        theme=theme,
    )


def _curated_team_member_card(member: object, member_links: list[object], *, theme: str) -> object:
    name = str(getattr(member, "name", member.get("name", "") if isinstance(member, dict) else "")).strip()
    role = str(getattr(member, "role", member.get("role", "") if isinstance(member, dict) else "")).strip()
    src = str(getattr(member, "image", member.get("src", member.get("image", "")) if isinstance(member, dict) else "")).strip()
    children: list[object] = [
        ui.Avatar(
            src,
            alt=name,
            size="72px",
            styles={"border": "3px solid rgba(255,255,255,0.9)", "box-shadow": "0 10px 18px rgba(67, 54, 43, 0.12)"},
        ),
        ui.Spacer("12px"),
        ui.Heading(name, level="small", theme=theme, styles={"font-size": "18px", "line-height": "1.25"}),
    ]
    if role:
        children.extend([ui.Spacer("6px"), ui.Text(role, size="small", theme=theme, styles={"color": "#7a6858"})])
    if member_links:
        children.extend([ui.Spacer("12px"), _curated_team_social_row(member_links, theme=theme)])
    return ui.raw(
        render_tag(
            "table",
            attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
            styles={
                "width": "100%",
                "border-radius": "22px",
                "border": "1px solid #e7d9ca",
                "background": "#fffdfa",
                "box-shadow": "0 12px 24px rgba(67, 54, 43, 0.08)",
            },
            children=[
                ui.raw(
                    render_tag(
                        "tr",
                        children=[
                            render_tag(
                                "td",
                                styles={"padding": "24px 18px", "text-align": "center"},
                                children=children,
                            )
                        ],
                    )
                )
            ],
        )
    )


@dataclass(frozen=True)
class ExampleSpec:
    slug: str
    code: str
    factory: Callable[[], object]
    description: str


def common_kwargs(theme: str = "default") -> str:
    return f"theme='{theme}'"


EXAMPLES: dict[str, ExampleSpec] = {
    "EmailDocument": ExampleSpec(
        slug="email-document-shell",
        description="A full document combining reusable sections and explicit metadata.",
        code=dedent(
            """
            from pyzahidal import ActionSpec, EmailDocument, Hero, CallToAction

            doc = EmailDocument(
                sections=[
                    Hero(
                        eyebrow="Launch week",
                        title="Ship polished email UI",
                        body="Compose from reusable blocks.",
                        primary_action=ActionSpec("Explore", href="#"),
                    ),
                    CallToAction(
                        "Need a custom flow?",
                        "Start from the document shell and mix sections freely.",
                        [ActionSpec("Read docs", href="#", variant="primary")],
                    ),
                ],
                preview_text="Compose polished email UI",
                title="pyzahidal docs",
                theme="modern",
            )
            """
        ).strip(),
        factory=lambda: ui.EmailDocument(
            sections=[
                ui.Hero(
                    eyebrow="Launch week",
                    title="Ship polished email UI",
                    body="Compose from reusable blocks.",
                    primary_action=_action_spec("Explore", href="#"),
                    theme="modern",
                ),
                ui.CallToAction(
                    "Need a custom flow?",
                    "Start from the document shell and mix sections freely.",
                    [_action_spec("Read docs", href="#", variant="primary")],
                    theme="modern",
                ),
            ],
            preview_text="Compose polished email UI",
            title="pyzahidal docs",
            theme="modern",
        ),
    ),
    "Alert": ExampleSpec(
        slug="alert-info",
        description="A short informational announcement.",
        code='from pyzahidal import Alert, Text\n\ncomponent = Alert(Text("Deployment scheduled for 18:00 UTC"), tone="info", theme="modern")',
        factory=lambda: ui.Alert(ui.Text("Deployment scheduled for 18:00 UTC", theme="modern"), tone="info", theme="modern"),
    ),
    "Avatar": ExampleSpec(
        slug="avatar-profile",
        description="A single profile image token.",
        code=f'from pyzahidal import Avatar\n\ncomponent = Avatar(src={code_string_literal(svg_data_url("A", 56, 56, "#fee2e2", "#b91c1c"))}, alt="Avery", size="56px")',
        factory=lambda: ui.Avatar(svg_data_url("A", 56, 56, "#fee2e2", "#b91c1c"), alt="Avery", size="56px"),
    ),
    "AvatarGroup": ExampleSpec(
        slug="avatar-group",
        description="An overlapping row of avatars for social proof or team presence.",
        code=(
            'from pyzahidal import AvatarGroup, AvatarSpec\n\ncomponent = AvatarGroup(['
            f'AvatarSpec({code_string_literal(svg_data_url("A", 56, 56, "#fee2e2", "#b91c1c"))}, alt="Avery"), '
            f'AvatarSpec({code_string_literal(svg_data_url("N", 56, 56, "#fef3c7", "#b45309"))}, alt="Nina"), '
            f'AvatarSpec({code_string_literal(svg_data_url("K", 56, 56, "#dbeafe", "#1d4ed8"))}, alt="Kai")'
            '], size="44px")'
        ),
        factory=lambda: ui.AvatarGroup(
            [
                _avatar_spec(svg_data_url("A", 56, 56, "#fee2e2", "#b91c1c"), alt="Avery"),
                _avatar_spec(svg_data_url("N", 56, 56, "#fef3c7", "#b45309"), alt="Nina"),
                _avatar_spec(svg_data_url("K", 56, 56, "#dbeafe", "#1d4ed8"), alt="Kai"),
            ],
            size="44px",
        ),
    ),
    "Button": ExampleSpec(
        slug="button-primary",
        description="Primary CTA styling using theme tokens.",
        code='from pyzahidal import Button\n\ncomponent = Button("Open dashboard", href="https://example.com", theme="editorial")',
        factory=lambda: ui.Button("Open dashboard", href="https://example.com", theme="editorial"),
    ),
    "Column": ExampleSpec(
        slug="column-layout",
        description="A two-column layout inside a row.",
        code=dedent(
            """
            from pyzahidal import Column, Row, Section, Text

            component = Section(
                Row(
                    Column(Text("Left column"), width="55%"),
                    Column(Text("Right column"), width="45%"),
                ),
                theme="default",
            )
            """
        ).strip(),
        factory=lambda: ui.Section(
            ui.Row(
                ui.Column(ui.Text("Left column", theme="default"), width="55%"),
                ui.Column(ui.Text("Right column", theme="default"), width="45%"),
            ),
            theme="default",
        ),
    ),
    "Columns": ExampleSpec(
        slug="columns-layout",
        description="An uneven two-column layout without explicit `Column` wrappers.",
        code='from pyzahidal import Columns, Surface, Text\n\ncomponent = Surface(Columns(Text("Primary content"), Text("Sidebar"), widths=["65%", "35%"]), padding="20px", theme="modern")',
        factory=lambda: ui.Surface(
            ui.Columns(
                ui.Text("Primary content", theme="modern"),
                ui.Text("Sidebar", theme="modern", align="right"),
                widths=["65%", "35%"],
            ),
            padding="20px",
            theme="modern",
        ),
    ),
    "Container": ExampleSpec(
        slug="container-surface",
        description="A generic themed surface with custom child content.",
        code='from pyzahidal import Container, Section, Heading, Text\n\ncomponent = Container(Section(Heading("Container"), Text("Use this as a flexible wrapper.")))',
        factory=lambda: ui.Container(
            ui.Section(
                ui.Heading("Container", theme="default"),
                ui.Spacer("8px"),
                ui.Text("Use this as a flexible wrapper.", theme="default"),
                theme="default",
            ),
            theme="default",
        ),
    ),
    "DataTable": ExampleSpec(
        slug="data-table-orders",
        description="A compact orders-style table.",
        code='from pyzahidal import DataTable\n\ncomponent = DataTable(headers=["Item", "Qty"], rows=[["Pen", 2], ["Notebook", 1]], theme="commerce")',
        factory=lambda: ui.DataTable(headers=["Item", "Qty"], rows=[["Pen", 2], ["Notebook", 1]], theme="commerce"),
    ),
    "Divider": ExampleSpec(
        slug="divider-basic",
        description="A theme-aware divider between content blocks.",
        code='from pyzahidal import Divider\n\ncomponent = Divider(theme="default")',
        factory=lambda: ui.Divider(theme="default"),
    ),
    "Heading": ExampleSpec(
        slug="heading-display",
        description="A section-level heading.",
        code='from pyzahidal import Heading\n\ncomponent = Heading("Quarterly product recap", theme="editorial")',
        factory=lambda: ui.Heading("Quarterly product recap", theme="editorial"),
    ),
    "IconLink": ExampleSpec(
        slug="icon-link",
        description="A circular social-style icon tile.",
        code=f'from pyzahidal import IconLink\n\ncomponent = IconLink(href="#", icon_src={code_string_literal(svg_data_url("D", 20, 20, "#dbeafe", "#1d4ed8"))}, alt="Docs", theme="modern")',
        factory=lambda: ui.IconLink(href="#", icon_src=svg_data_url("D", 20, 20, "#dbeafe", "#1d4ed8"), alt="Docs", theme="modern"),
    ),
    "Image": ExampleSpec(
        slug="image-hero",
        description="A responsive image with rounded corners.",
        code=f'from pyzahidal import Image\n\ncomponent = Image(src={code_string_literal(svg_data_url("Release", 640, 280, "#e0f2fe", "#0369a1"))}, alt="Release art", width="100%", theme="modern")',
        factory=lambda: ui.Image(svg_data_url("Release", 640, 280, "#e0f2fe", "#0369a1"), alt="Release art", width="100%", theme="modern"),
    ),
    "ImageGroup": ExampleSpec(
        slug="image-group",
        description="A masonry-style image cluster for gallery and product layouts.",
        code=(
            'from pyzahidal import ImageGroup, ImageSpec\n\ncomponent = ImageGroup(items=['
            f'ImageSpec({code_string_literal(svg_data_url("One", 320, 240, "#dbeafe", "#1d4ed8"))}, alt="One"), '
            f'ImageSpec({code_string_literal(svg_data_url("Two", 320, 320, "#bfdbfe", "#1d4ed8"))}, alt="Two"), '
            f'ImageSpec({code_string_literal(svg_data_url("Three", 320, 260, "#93c5fd", "#1d4ed8"))}, alt="Three")'
            '], columns=2, masonry=True, theme="modern")'
        ),
        factory=lambda: ui.ImageGroup(
            items=[
                _image_spec(svg_data_url("One", 320, 240, "#dbeafe", "#1d4ed8"), alt="One"),
                _image_spec(svg_data_url("Two", 320, 320, "#bfdbfe", "#1d4ed8"), alt="Two"),
                _image_spec(svg_data_url("Three", 320, 260, "#93c5fd", "#1d4ed8"), alt="Three"),
            ],
            columns=2,
            masonry=True,
            theme="modern",
        ),
    ),
    "Inline": ExampleSpec(
        slug="inline-items",
        description="Inline items with shared spacing.",
        code='from pyzahidal import Inline, Pill\n\ncomponent = Inline(Pill("New"), Pill("Popular"), Pill("Beta"), theme="default")',
        factory=lambda: ui.Inline(ui.Pill("New", theme="default"), ui.Pill("Popular", theme="default"), ui.Pill("Beta", theme="default"), theme="default"),
    ),
    "Link": ExampleSpec(
        slug="text-link",
        description="A plain text link that follows theme colors.",
        code='from pyzahidal import Link\n\ncomponent = Link("Read changelog", href="#", theme="editorial")',
        factory=lambda: ui.Link("Read changelog", href="#", theme="editorial"),
    ),
    "LogoStrip": ExampleSpec(
        slug="logo-strip",
        description="A boxed logo cluster with text-only fallback.",
        code='from pyzahidal import LogoSpec, LogoStrip\n\ncomponent = LogoStrip([LogoSpec("Northwind"), LogoSpec("Acme"), LogoSpec("Studio Zero")], boxed=True, theme="default")',
        factory=lambda: ui.LogoStrip([_logo_spec("Northwind"), _logo_spec("Acme"), _logo_spec("Studio Zero")], boxed=True, theme="default"),
    ),
    "Menu": ExampleSpec(
        slug="menu-links",
        description="Horizontal navigation composed from simple items.",
        code='from pyzahidal import Menu, MenuItemSpec\n\ncomponent = Menu([MenuItemSpec("Docs", href="#"), MenuItemSpec("Pricing", href="#"), MenuItemSpec("Support", href="#")], theme="modern")',
        factory=lambda: ui.Menu([_menu_item_spec("Docs"), _menu_item_spec("Pricing"), _menu_item_spec("Support")], theme="modern"),
    ),
    "Metric": ExampleSpec(
        slug="metric-stat",
        description="A KPI value with supporting copy and trend.",
        code='from pyzahidal import Metric\n\ncomponent = Metric("55k", label="API calls/month", detail="Across all workspaces", trend="+25%", theme="modern")',
        factory=lambda: ui.Metric("55k", label="API calls/month", detail="Across all workspaces", trend="+25%", theme="modern"),
    ),
    "Nav": ExampleSpec(
        slug="nav-custom",
        description="A low-level custom navigation wrapper.",
        code='from pyzahidal import Nav, raw\n\ncomponent = Nav(raw(\'<a href="#home">Home</a> <a href="#docs">Docs</a>\'), styles={"font-family": "Arial"})',
        factory=lambda: ui.Nav(ui.raw('<a href="#home">Home</a> <a href="#docs">Docs</a>'), styles={"font-family": "Arial, Helvetica, sans-serif"}),
    ),
    "Pill": ExampleSpec(
        slug="pill-status",
        description="A compact label for status or classification.",
        code='from pyzahidal import Pill\n\ncomponent = Pill("Beta", theme="vibrant")',
        factory=lambda: ui.Pill("Beta", theme="vibrant"),
    ),
    "ProgressBar": ExampleSpec(
        slug="progress-bar",
        description="A progress indicator used in order or onboarding flows.",
        code='from pyzahidal import ProgressBar\n\ncomponent = ProgressBar(72, theme="modern")',
        factory=lambda: ui.ProgressBar(72, theme="modern"),
    ),
    "Row": ExampleSpec(
        slug="row-two-columns",
        description="A horizontal row with two text columns.",
        code='from pyzahidal import Row, Column, Text\n\ncomponent = Row(Column(Text("Plan")), Column(Text("$29/month")))',
        factory=lambda: ui.Row(
            ui.Column(ui.Text("Plan", theme="default"), width="50%"),
            ui.Column(ui.Text("$29/month", theme="default"), width="50%", styles={"text-align": "right"}),
        ),
    ),
    "Section": ExampleSpec(
        slug="section-copy",
        description="A padded content section.",
        code='from pyzahidal import Section, Heading, Text\n\ncomponent = Section(Heading("Section title"), Text("Everything inside inherits the section padding."), theme="default")',
        factory=lambda: ui.Section(
            ui.Heading("Section title", theme="default"),
            ui.Spacer("8px"),
            ui.Text("Everything inside inherits the section padding.", theme="default"),
            theme="default",
        ),
    ),
    "Stack": ExampleSpec(
        slug="stack-layout",
        description="Vertical composition without manual spacer components.",
        code='from pyzahidal import Stack, Heading, Text\n\ncomponent = Stack(Heading("Stack title"), Text("Each child gets consistent spacing."), gap="12px", theme="default")',
        factory=lambda: ui.Stack(ui.Heading("Stack title", theme="default"), ui.Text("Each child gets consistent spacing.", theme="default"), gap="12px", theme="default"),
    ),
    "Surface": ExampleSpec(
        slug="surface-panel",
        description="An image-backed promo hero composed from nested surfaces and an overlay card.",
        code='from pyzahidal import Button, Inline, Spacer, Stack, Surface, Heading, Text\n\ncomponent = Surface(Surface(Stack(Heading("Your upgrade starts here!", level="hero", tone="inverse", align="center"), Text("Step into the next generation of innovation. Sleek design, pro-level performance, and features that keep you ahead of the curve.", tone="inverse", align="center"), Inline(Button("Sign up now", href="#", theme_overrides={"primary_color": "#5b5cf0", "primary_text_color": "#ffffff"}), Button("Discover more", href="#", variant="ghost", styles={"color": "#ffffff", "border": "1px solid #ffffff"}, theme="modern"), align="center", gap="16px"), gap="20px", theme="modern"), tone="overlay", padding="56px 44px", radius="12px", theme="modern"), background_image="https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=1400&q=80", background_color="#1f2937", padding="30px", radius="24px", theme="modern")',
        factory=lambda: ui.Surface(
            ui.Surface(
                ui.Stack(
                    ui.Heading("Your upgrade starts here!", level="hero", tone="inverse", align="center", theme="modern"),
                    ui.Text(
                        "Step into the next generation of innovation. Sleek design, pro-level performance, and features that keep you ahead of the curve.",
                        tone="inverse",
                        align="center",
                        theme="modern",
                    ),
                    ui.Inline(
                        ui.Button(
                            "Sign up now",
                            href="#",
                            theme="modern",
                            theme_overrides={"primary_color": "#5b5cf0", "primary_text_color": "#ffffff"},
                        ),
                        ui.Button(
                            "Discover more",
                            href="#",
                            variant="ghost",
                            styles={"color": "#ffffff", "border": "1px solid #ffffff"},
                            theme="modern",
                        ),
                        align="center",
                        gap="16px",
                        theme="modern",
                    ),
                    gap="20px",
                    theme="modern",
                ),
                tone="overlay",
                padding="56px 44px",
                radius="12px",
                theme="modern",
            ),
            background_image="https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=1400&q=80",
            background_color="#1f2937",
            padding="30px",
            radius="24px",
            theme="modern",
        ),
    ),
    "SocialLinks": ExampleSpec(
        slug="social-links",
        description="Text links suitable for footers or utility bars.",
        code='from pyzahidal import SocialLinkSpec, SocialLinks\n\ncomponent = SocialLinks([SocialLinkSpec(label="GitHub", href="#"), SocialLinkSpec(label="Docs", href="#")], theme="default")',
        factory=lambda: ui.SocialLinks([_social_link_spec(label="GitHub"), _social_link_spec(label="Docs")], theme="default"),
    ),
    "Spacer": ExampleSpec(
        slug="spacer-gap",
        description="A vertical gap component.",
        code='from pyzahidal import Spacer\n\ncomponent = Spacer("32px")',
        factory=lambda: ui.Spacer("32px"),
    ),
    "Text": ExampleSpec(
        slug="text-body",
        description="Plain body copy with theme-aware color and type.",
        code='from pyzahidal import Text\n\ncomponent = Text("This copy uses the active body text styles.", theme="editorial")',
        factory=lambda: ui.Text("This copy uses the active body text styles.", theme="editorial"),
    ),
    "BentoGrid": ExampleSpec(
        slug="bento-grid",
        description="Stacked campaign cards with distinct backgrounds.",
        code='from pyzahidal import BentoGrid, BentoItemSpec\n\ncomponent = BentoGrid(items=[BentoItemSpec("Sync", "Keep sales and product aligned."), BentoItemSpec("Ship", "Generate launch-ready email blocks.")], theme="modern")',
        factory=lambda: ui.BentoGrid(
            items=[
                ui.BentoItemSpec("Sync", "Keep sales and product aligned."),
                ui.BentoItemSpec("Ship", "Generate launch-ready email blocks."),
            ],
            theme="modern",
        ),
    ),
    "BlogList": ExampleSpec(
        slug="blog-list",
        description="A simple editorial listing.",
        code='from pyzahidal import BlogList, BlogPostSpec\n\ncomponent = BlogList(posts=[BlogPostSpec("A quieter changelog", "What changed and why.", href="#"), BlogPostSpec("Migration notes", "Upgrade without breaking your templates.", href="#")], theme="editorial")',
        factory=lambda: ui.BlogList(
            posts=[
                ui.BlogPostSpec("A quieter changelog", "What changed and why.", href="#"),
                ui.BlogPostSpec("Migration notes", "Upgrade without breaking your templates.", href="#"),
            ],
            theme="editorial",
        ),
    ),
    "CallToAction": ExampleSpec(
        slug="call-to-action",
        description="A concise prompt with one next step.",
        code='from pyzahidal import ActionSpec, CallToAction\n\ncomponent = CallToAction("Ready to migrate?", "Start with the generated docs.", [ActionSpec("Read the guide", href="#", variant="primary"), ActionSpec("Browse examples", href="#", variant="ghost")], theme="modern")',
        factory=lambda: ui.CallToAction(
            "Ready to migrate?",
            "Start with the generated docs.",
            [_action_spec("Read the guide", href="#", variant="primary"), _action_spec("Browse examples", href="#", variant="ghost")],
            theme="modern",
        ),
    ),
    "CategoryPreview": ExampleSpec(
        slug="category-preview",
        description="A titled set of category jump links.",
        code='from pyzahidal import CategoryPreview\n\ncomponent = CategoryPreview("Browse by team", [("Product", "#"), ("Marketing", "#"), ("Support", "#")], theme="default")',
        factory=lambda: ui.CategoryPreview("Browse by team", [("Product", "#"), ("Marketing", "#"), ("Support", "#")], theme="default"),
    ),
    "Coupon": ExampleSpec(
        slug="coupon",
        description="A focused promo code block.",
        code='from pyzahidal import Coupon\n\ncomponent = Coupon("SPRING20", "Valid on annual plans through Friday.", theme="commerce")',
        factory=lambda: ui.Coupon("SPRING20", "Valid on annual plans through Friday.", theme="commerce"),
    ),
    "FAQ": ExampleSpec(
        slug="faq",
        description="A short frequently asked questions list.",
        code='from pyzahidal import FAQ, FaqItemSpec\n\ncomponent = FAQ([FaqItemSpec("Does it support Jinja?", "Yes, raw placeholders are preserved."), FaqItemSpec("Can I override themes?", "Yes, pass theme_overrides.")], theme="default")',
        factory=lambda: ui.FAQ(
            [_faq_spec("Does it support Jinja?", "Yes, raw placeholders are preserved."), _faq_spec("Can I override themes?", "Yes, pass theme_overrides.")],
            theme="default",
        ),
    ),
    "Feature": ExampleSpec(
        slug="feature",
        description="A single feature spotlight.",
        code='from pyzahidal import Feature\n\ncomponent = Feature("Composable blocks", "Mix primitives and sections without leaving Python.", icon="◆", theme="modern")',
        factory=lambda: ui.Feature("Composable blocks", "Mix primitives and sections without leaving Python.", icon="◆", theme="modern"),
    ),
    "Footer": ExampleSpec(
        slug="footer",
        description="Brand, social links, and opt-in copy.",
        code='from pyzahidal import Footer, SocialLinkSpec\n\ncomponent = Footer("Acme Studio", [SocialLinkSpec(label="GitHub", href="#"), SocialLinkSpec(label="Support", href="#")], theme="editorial")',
        factory=lambda: ui.Footer("Acme Studio", [_social_link_spec(label="GitHub"), _social_link_spec(label="Support")], theme="editorial"),
    ),
    "Header": ExampleSpec(
        slug="header",
        description="A branded header with optional nav items.",
        code='from pyzahidal import Header, MenuItemSpec\n\ncomponent = Header("Acme Studio", [MenuItemSpec("Docs", href="#"), MenuItemSpec("Pricing", href="#")], theme="modern")',
        factory=lambda: ui.Header("Acme Studio", [_menu_item_spec("Docs"), _menu_item_spec("Pricing")], theme="modern"),
    ),
    "Hero": ExampleSpec(
        slug="hero",
        description="Primary campaign section with optional image.",
        code=(
            'from pyzahidal import ActionSpec, Hero, HeroMediaSpec, MetricSpec\n\ncomponent = Hero('
            'eyebrow="Launch week", title="Email UI that stays composable", '
            'body="Primitives, sections, and starter templates in one library.", '
            'primary_action=ActionSpec("Explore", href="#", variant="primary"), '
            'secondary_action=ActionSpec("See templates", href="#", variant="secondary"), '
            f'media=HeroMediaSpec({code_string_literal(svg_data_url("Launch", 640, 260, "#dbeafe", "#1d4ed8"))}, title="Preview card", body="Pair the hero copy with framed media."), '
            'meta_items=[MetricSpec(label="Open rate", value="58%"), MetricSpec(label="CTR", value="9.1%")], theme="modern")'
        ),
        factory=lambda: ui.Hero(
            eyebrow="Launch week",
            title="Email UI that stays composable",
            body="Primitives, sections, and starter templates in one library.",
            primary_action=_action_spec("Explore", href="#", variant="primary"),
            secondary_action=_action_spec("See templates", href="#", variant="secondary"),
            media=ui.HeroMediaSpec(
                svg_data_url("Launch", 640, 260, "#dbeafe", "#1d4ed8"),
                title="Preview card",
                body="Pair the hero copy with framed media.",
            ),
            meta_items=[_metric_spec("Open rate", "58%"), _metric_spec("CTR", "9.1%")],
            theme="modern",
        ),
    ),
    "LogoCloud": ExampleSpec(
        slug="logo-cloud",
        description="A cluster of customer or partner labels.",
        code='from pyzahidal import LogoCloud, LogoSpec\n\ncomponent = LogoCloud([LogoSpec("Northwind"), LogoSpec("Acme"), LogoSpec("Studio Zero")], theme="default")',
        factory=lambda: ui.LogoCloud([_logo_spec("Northwind"), _logo_spec("Acme"), _logo_spec("Studio Zero")], theme="default"),
    ),
    "OrderSummary": ExampleSpec(
        slug="order-summary",
        description="Summary rows with optional delivery progress.",
        code='from pyzahidal import OrderSummary\n\ncomponent = OrderSummary([("Subtotal", "$40"), ("Shipping", "$5"), ("Total", "$45")], progress=50, theme="commerce")',
        factory=lambda: ui.OrderSummary([("Subtotal", "$40"), ("Shipping", "$5"), ("Total", "$45")], progress=50, theme="commerce"),
    ),
    "Pricing": ExampleSpec(
        slug="pricing",
        description="Multiple plan cards with CTA buttons.",
        code='from pyzahidal import ActionSpec, Pricing, PricingPlanSpec\n\ncomponent = Pricing(plans=[PricingPlanSpec("Starter", "$9", "For early experiments.", features=["1 seat", "Docs access"], action=ActionSpec("Choose starter", href="#", variant="secondary")), PricingPlanSpec("Scale", "$29", "For growing teams.", badge="Most popular", featured=True, features=["Unlimited seats", "Shared workspace", "Priority support"], action=ActionSpec("Choose scale", href="#", variant="primary"))], theme="modern")',
        factory=lambda: ui.Pricing(
            plans=[
                ui.PricingPlanSpec("Starter", "$9", "For early experiments.", features=["1 seat", "Docs access"], action=_action_spec("Choose starter", href="#", variant="secondary")),
                ui.PricingPlanSpec("Scale", "$29", "For growing teams.", badge="Most popular", featured=True, features=["Unlimited seats", "Shared workspace", "Priority support"], action=_action_spec("Choose scale", href="#", variant="primary")),
            ],
            theme="modern",
        ),
    ),
    "ProductDetail": ExampleSpec(
        slug="product-detail",
        description="A focused product block with image and pricing.",
        code=f'from pyzahidal import ProductDetail\n\ncomponent = ProductDetail("Desk Lamp", "$49", "Warm light with a low-profile base.", image_src={code_string_literal(svg_data_url("Lamp", 640, 260, "#ffedd5", "#9a3412"))}, theme="commerce")',
        factory=lambda: ui.ProductDetail(
            "Desk Lamp",
            "$49",
            "Warm light with a low-profile base.",
            image_src=svg_data_url("Lamp", 640, 260, "#ffedd5", "#9a3412"),
            theme="commerce",
        ),
    ),
    "ProductFeatures": ExampleSpec(
        slug="product-features",
        description="Bullet-like feature list.",
        code='from pyzahidal import ProductFeatures\n\ncomponent = ProductFeatures(["Frictionless setup", "Jinja-friendly output", "Theme presets"], theme="default")',
        factory=lambda: ui.ProductFeatures(["Frictionless setup", "Jinja-friendly output", "Theme presets"], theme="default"),
    ),
    "ProductList": ExampleSpec(
        slug="product-list",
        description="Multiple product summaries in sequence.",
        code='from pyzahidal import ProductList, ProductSpec\n\ncomponent = ProductList(products=[ProductSpec("Desk Lamp", "$49", "Warm light"), ProductSpec("Bulb", "$9", "Spare part")], theme="commerce")',
        factory=lambda: ui.ProductList(
            products=[
                ui.ProductSpec("Desk Lamp", "$49", "Warm light"),
                ui.ProductSpec("Bulb", "$9", "Spare part"),
            ],
            theme="commerce",
        ),
    ),
    "Reviews": ExampleSpec(
        slug="reviews",
        description="Review cards driven by the testimonial layout.",
        code='from pyzahidal import ReviewSpec, Reviews\n\ncomponent = Reviews([ReviewSpec(quote="Cut our email build time in half.", author="Sam, Product Ops")], theme="default")',
        factory=lambda: ui.Reviews([ui.ReviewSpec(quote="Cut our email build time in half.", author="Sam, Product Ops")], theme="default"),
    ),
    "ShoppingCart": ExampleSpec(
        slug="shopping-cart",
        description="Cart rows rendered through the shared table primitive.",
        code='from pyzahidal import CartItemSpec, ShoppingCart\n\ncomponent = ShoppingCart([CartItemSpec("Desk Lamp", "1", "$49"), CartItemSpec("Bulb", "2", "$18")], theme="commerce")',
        factory=lambda: ui.ShoppingCart(
            [ui.CartItemSpec("Desk Lamp", "1", "$49"), ui.CartItemSpec("Bulb", "2", "$18")],
            theme="commerce",
        ),
    ),
    "Stats": ExampleSpec(
        slug="stats",
        description="Compact headline metrics.",
        code='from pyzahidal import MetricSpec, Stats\n\ncomponent = Stats([MetricSpec(label="Open rate", value="51%", detail="Across the last 5 sends"), MetricSpec(label="CTR", value="8.2%", detail="Driven by stronger CTAs"), MetricSpec(label="Revenue", value="$12k", detail="Attributed this month")], theme="modern")',
        factory=lambda: ui.Stats(
            [
                _metric_spec("Open rate", "51%", "Across the last 5 sends"),
                _metric_spec("CTR", "8.2%", "Driven by stronger CTAs"),
                _metric_spec("Revenue", "$12k", "Attributed this month"),
            ],
            theme="modern",
        ),
    ),
    "Team": ExampleSpec(
        slug="team",
        description="A simple member listing.",
        code=(
            'from pyzahidal import Team, TeamMemberSpec\n\ncomponent = Team(['
            f'TeamMemberSpec(name="Avery", role="Design", image={code_string_literal(svg_data_url("A", 56, 56, "#ede9fe", "#6d28d9"))}), '
            f'TeamMemberSpec(name="Kai", role="Engineering", image={code_string_literal(svg_data_url("K", 56, 56, "#dcfce7", "#166534"))})'
            '], theme="default")'
        ),
        factory=lambda: ui.Team(
            [
                ui.TeamMemberSpec(name="Avery", role="Design", image=svg_data_url("A", 56, 56, "#ede9fe", "#6d28d9")),
                ui.TeamMemberSpec(name="Kai", role="Engineering", image=svg_data_url("K", 56, 56, "#dcfce7", "#166534")),
            ],
            theme="default",
        ),
    ),
    "Testimonials": ExampleSpec(
        slug="testimonials",
        description="Customer or stakeholder quotes.",
        code='from pyzahidal import TestimonialSpec, Testimonials\n\ncomponent = Testimonials([TestimonialSpec("The generated docs made adoption much easier.", "Nina, Growth")], theme="editorial")',
        factory=lambda: ui.Testimonials([ui.TestimonialSpec("The generated docs made adoption much easier.", "Nina, Growth")], theme="editorial"),
    ),
    "Timeline": ExampleSpec(
        slug="timeline",
        description="A changelog-style timeline with release metadata.",
        code='from pyzahidal import Timeline, TimelineStepSpec\n\ncomponent = Timeline([TimelineStepSpec("v1.0.9", "19 Jan", "Refactoring", "Refined layouts", "Introduced a new timeline pattern to clearly represent ordered states and progression."), TimelineStepSpec("v1.1.0", "21 Jan", "Performance", "Faster rendering", "Reduced template rendering overhead for large campaign payloads.")], theme="modern")',
        factory=lambda: ui.Timeline(
            [
                _timeline_step_spec("v1.0.9", "19 Jan", "Refactoring", "Refined layouts", "Introduced a new timeline pattern to clearly represent ordered states and progression."),
                _timeline_step_spec("v1.1.0", "21 Jan", "Performance", "Faster rendering", "Reduced template rendering overhead for large campaign payloads."),
            ],
            theme="modern",
        ),
    ),
    "WelcomeHero": ExampleSpec(
        slug="welcome-hero",
        description="A centered welcome block with overlapped team avatars and a confirmation CTA.",
        code=(
            'from pyzahidal import ActionSpec, AvatarSpec, WelcomeHero\n\ncomponent = WelcomeHero('
            'title="The team welcomes you!", '
            'body="Your workspace is ready — confirm your email to join your team, collaborate seamlessly, and get started today.", '
            'action=ActionSpec("Confirm your email", href="#"), members=['
            f'AvatarSpec({code_string_literal(svg_data_url("A", 56, 56, "#d1d5db", "#374151"))}, alt="Avery", name="Avery"), '
            f'AvatarSpec({code_string_literal(svg_data_url("N", 56, 56, "#fde68a", "#92400e"))}, alt="Nina", name="Nina"), '
            f'AvatarSpec({code_string_literal(svg_data_url("K", 56, 56, "#bfdbfe", "#1d4ed8"))}, alt="Kai", name="Kai"), '
            f'AvatarSpec({code_string_literal(svg_data_url("L", 56, 56, "#fecdd3", "#9f1239"))}, alt="Lena", name="Lena")'
            '], theme="modern")'
        ),
        factory=lambda: ui.WelcomeHero(
            title="The team welcomes you!",
            body="Your workspace is ready — confirm your email to join your team, collaborate seamlessly, and get started today.",
            action=_action_spec("Confirm your email", href="#"),
            members=[
                _avatar_spec(svg_data_url("A", 56, 56, "#d1d5db", "#374151"), alt="Avery", name="Avery"),
                _avatar_spec(svg_data_url("N", 56, 56, "#fde68a", "#92400e"), alt="Nina", name="Nina"),
                _avatar_spec(svg_data_url("K", 56, 56, "#bfdbfe", "#1d4ed8"), alt="Kai", name="Kai"),
                _avatar_spec(svg_data_url("L", 56, 56, "#fecdd3", "#9f1239"), alt="Lena", name="Lena"),
            ],
            theme="modern",
        ),
    ),
    "MarketingTemplate": ExampleSpec(
        slug="marketing-template",
        description="A starter document for launch campaigns.",
        code='from pyzahidal import MarketingTemplate\n\ndoc = MarketingTemplate(brand="Acme Studio", hero_title="Ship clearer launch emails", hero_body="Compose from reusable blocks and theme presets.", cta_label="Explore docs", theme="modern")',
        factory=lambda: ui.MarketingTemplate(
            brand="Acme Studio",
            hero_title="Ship clearer launch emails",
            hero_body="Compose from reusable blocks and theme presets.",
            cta_label="Explore docs",
            theme="modern",
        ),
    ),
    "NewsletterTemplate": ExampleSpec(
        slug="newsletter-template",
        description="A starter document for editorial roundups.",
        code='from pyzahidal import BlogPostSpec, NewsletterTemplate\n\ndoc = NewsletterTemplate(brand="Acme Studio", posts=[BlogPostSpec("Composable email patterns", "A tour through the component library.", href="#"), BlogPostSpec("Theme tokens in practice", "How to keep brand styling consistent.", href="#")], theme="editorial")',
        factory=lambda: ui.NewsletterTemplate(
            brand="Acme Studio",
            posts=[
                ui.BlogPostSpec("Composable email patterns", "A tour through the component library.", href="#"),
                ui.BlogPostSpec("Theme tokens in practice", "How to keep brand styling consistent.", href="#"),
            ],
            theme="editorial",
        ),
    ),
    "OrderTemplate": ExampleSpec(
        slug="order-template",
        description="A starter document for order updates.",
        code='from pyzahidal import OrderTemplate\n\ndoc = OrderTemplate(brand="Acme Store", summary_rows=[("Order", "#1042"), ("Status", "Packed"), ("Total", "$45")], theme="commerce")',
        factory=lambda: ui.OrderTemplate(
            brand="Acme Store",
            summary_rows=[("Order", "#1042"), ("Status", "Packed"), ("Total", "$45")],
            theme="commerce",
        ),
    ),
    "ProductAnnouncementTemplate": ExampleSpec(
        slug="product-announcement-template",
        description="A starter document for product releases.",
        code=(
            'from pyzahidal import ProductAnnouncementTemplate, ProductSpec\n\n'
            'doc = ProductAnnouncementTemplate(brand="Acme Store", '
            f'product=ProductSpec("Desk Lamp", "$49", "Warm light", image_src={code_string_literal(svg_data_url("Lamp", 640, 260, "#ffedd5", "#9a3412"))}, '
            'features=["Warm tone", "Low-profile base", "Energy efficient LED"]), '
            'related=[ProductSpec("Bulb", "$9", "Spare part")], theme="commerce")'
        ),
        factory=lambda: ui.ProductAnnouncementTemplate(
            brand="Acme Store",
            product=ui.ProductSpec(
                "Desk Lamp",
                "$49",
                "Warm light",
                image_src=svg_data_url("Lamp", 640, 260, "#ffedd5", "#9a3412"),
                features=["Warm tone", "Low-profile base", "Energy efficient LED"],
            ),
            related=[ui.ProductSpec("Bulb", "$9", "Spare part")],
            theme="commerce",
        ),
    ),
    "PromoTemplate": ExampleSpec(
        slug="promo-template",
        description="A starter document for timed promotional offers.",
        code='from pyzahidal import ActionSpec, PricingPlanSpec, PromoTemplate\n\ndoc = PromoTemplate(brand="Acme Store", code="SAVE20", detail="Use this through Friday.", plans=[PricingPlanSpec("Starter", "$9", "Single seat", features=["1 seat"], action=ActionSpec("Choose starter", href="#", variant="secondary")), PricingPlanSpec("Scale", "$29", "Team workspace", badge="Best value", featured=True, features=["Unlimited seats", "Shared workspace"], action=ActionSpec("Choose scale", href="#", variant="primary"))], theme="vibrant")',
        factory=lambda: ui.PromoTemplate(
            brand="Acme Store",
            code="SAVE20",
            detail="Use this through Friday.",
            plans=[
                ui.PricingPlanSpec("Starter", "$9", "Single seat", features=["1 seat"], action=_action_spec("Choose starter", href="#", variant="secondary")),
                ui.PricingPlanSpec("Scale", "$29", "Team workspace", badge="Best value", featured=True, features=["Unlimited seats", "Shared workspace"], action=_action_spec("Choose scale", href="#", variant="primary")),
            ],
            theme="vibrant",
        ),
    ),
}

THEME_SHOWCASES = {
    "Hero": lambda theme: ui.Hero(
        eyebrow="Theme preset",
        title=f"{theme.title()} hero",
        body="Compare tone, hierarchy, and framed media treatment across presets.",
        primary_action=_action_spec("View docs", href="#", variant="primary"),
        secondary_action=_action_spec("Browse themes", href="#", variant="secondary"),
        media=ui.HeroMediaSpec(
            svg_data_url(theme.title(), 640, 240, "#e2e8f0", "#334155"),
            title=f"{theme.title()} media card",
            body="The preview shell now matches the example theme.",
        ),
        meta_items=[_metric_spec("Actions", "3"), _metric_spec("Media frame", "1")],
        theme=theme,
    ),
    "Button": lambda theme: ui.Button("Open docs", href="#", theme=theme),
    "Pricing": lambda theme: ui.Pricing(
        plans=[
            ui.PricingPlanSpec("Starter", "$9", "Single seat", features=["1 seat", "Docs"], action=_action_spec("Choose starter", href="#", variant="secondary")),
            ui.PricingPlanSpec("Scale", "$29", "Team workspace", badge="Popular", featured=True, features=["Unlimited seats", "Priority support"], action=_action_spec("Choose scale", href="#", variant="primary")),
        ],
        theme=theme,
    ),
    "MarketingTemplate": lambda theme: ui.MarketingTemplate(
        brand="Acme Studio",
        hero_title=f"{theme.title()} launch",
        hero_body="One template, different preset personalities.",
        cta_label="View guide",
        theme=theme,
    ),
}


def canonical_names() -> list[str]:
    exports = [name for name in ui.__all__ if name not in SKIPPED_EXPORTS]
    return sorted(exports, key=lambda name: (list(GROUP_TITLES).index(GROUPS[name]), name))


def aliases_for(name: str) -> list[str]:
    return sorted(alias for alias, target in ALIASES.items() if target == name)


def signature_for(name: str) -> str:
    return f"{name}{inspect.signature(getattr(ui, name))}"


def option_lines(name: str) -> list[str]:
    params = inspect.signature(getattr(ui, name)).parameters.values()
    lines: list[str] = []
    for param in params:
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            lines.append(f"`*{param.name}`: child content items.")
            continue
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            lines.append(f"`**{param.name}`: forwarded HTML attributes or constructor-specific kwargs.")
            continue
        text = f"`{param.name}`"
        if param.default is not inspect._empty:
            text += f" default `{param.default!r}`"
        if param.kind is inspect.Parameter.KEYWORD_ONLY:
            text += " keyword-only"
        lines.append(f"{text}.")
    return lines


def infer_preview_theme(code: str) -> str:
    match = re.search(r'theme\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', code)
    return match.group(1) if match else "default"


def render_component_preview(component: object, title: str, description: str, preview_theme: str = "default") -> str:
    if isinstance(component, ui.EmailDocument):
        return component.render()
    document = ui.EmailDocument(sections=[component], preview_text=description, title=title, theme=preview_theme)
    return document.render()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def published_asset_path(relative_path: str, page_depth: int = 0) -> str:
    return f"{'../' * page_depth}{relative_path.lstrip('/')}"


def iframe(preview_html: str, relative_path: str, title: str, height: int = 540, page_depth: int = 0) -> str:
    return (
        '<div class="docs-preview-shell">'
        f'<iframe class="docs-preview-frame" src="{published_asset_path(relative_path, page_depth=page_depth)}" '
        f'srcdoc="{escape(preview_html, quote=True)}" title="{title}" '
        f'loading="lazy" scrolling="no" height="{height}"></iframe>'
        "</div>"
    )


def screenshot_markup(relative_path: str, alt: str, page_depth: int = 0) -> str:
    screenshot = ROOT / "docs" / relative_path
    if not screenshot.exists():
        return "_Screenshot asset not generated yet. Run `python -m scripts.docs` after installing the docs extras._"
    path = published_asset_path(relative_path, page_depth=page_depth)
    return f'<img alt="{alt}" src="{path}" />'


def example_height(name: str) -> int:
    return {
        "EmailDocument": 900,
        "Hero": 820,
        "Surface": 760,
        "MarketingTemplate": 920,
        "NewsletterTemplate": 1080,
        "OrderTemplate": 960,
        "ProductAnnouncementTemplate": 1080,
        "PromoTemplate": 1040,
        "Pricing": 920,
        "ProductList": 940,
        "OrderSummary": 760,
        "WelcomeHero": 760,
    }.get(name, 620)


def curated_showcase_path(slug: str) -> str:
    normalized = slug if slug.startswith("curated-") else f"curated-{slug}"
    return f"assets/examples/{normalized}.html"


def curated_showcase_screenshot_path(slug: str) -> str:
    normalized = slug if slug.startswith("curated-") else f"curated-{slug}"
    return f"assets/screenshots/{normalized}.png"


def curated_source_showcase_path(slug: str) -> str:
    normalized = slug if slug.startswith("curated-") else f"curated-{slug}"
    return f"assets/examples-source/{normalized}.html"


def curated_source_screenshot_path(slug: str) -> str:
    normalized = slug if slug.startswith("curated-") else f"curated-{slug}"
    return f"assets/screenshots-source/{normalized}.png"


def curated_visual_diff_path(slug: str) -> str:
    normalized = slug if slug.startswith("curated-") else f"curated-{slug}"
    return f"assets/screenshots-diff/{normalized}.png"


def _legacy_curated_examples() -> list[CuratedExampleSpec]:
    def spec(
        *,
        category: str,
        title: str,
        slug: str,
        description: str,
        code: str,
        factory: Callable[[], object],
        theme: str | None = None,
    ) -> CuratedExampleSpec:
        showcase_slug = f"curated-{slug}"
        return CuratedExampleSpec(
            category=category,
            title=title,
            slug=showcase_slug,
            description=description,
            code=code.strip(),
            factory=factory,
            theme=theme or curated_theme(category),
            screenshot_path=curated_showcase_screenshot_path(slug),
        )

    return [
        spec(
            category="Logos",
            title="Basic logo cloud",
            slug="logos-basic-logo-cloud",
            description="A centered payment-logo row rebuilt from lower-level primitives and inline assets.",
            code=dedent(
                f"""
                from pyzahidal import Heading, Inline, Section, Stack, Text, raw

                component = Section(
                    Stack(
                        Heading("Supported payment services", level="small", align="center", theme="default"),
                        Inline(
                            raw('<img src=' + {code_string_literal(code_string_literal(branded_logo_data_url("Stripe", 57, "#635bff", "#ffffff")))} + ' alt="Stripe" width="57" style="display:block" />'),
                            raw('<img src=' + {code_string_literal(code_string_literal(branded_logo_data_url("Apple Pay", 60, "#111827", "#ffffff")))} + ' alt="Apple Pay" width="60" style="display:block" />'),
                            raw('<img src=' + {code_string_literal(code_string_literal(branded_logo_data_url("Mastercard", 40, "#fff7ed", "#c2410c")))} + ' alt="Mastercard" width="40" style="display:block" />'),
                            raw('<img src=' + {code_string_literal(code_string_literal(branded_logo_data_url("Visa", 50, "#eff6ff", "#1d4ed8")))} + ' alt="Visa" width="50" style="display:block" />'),
                            raw('<img src=' + {code_string_literal(code_string_literal(branded_logo_data_url("Klarna", 70, "#fce7f3", "#9d174d")))} + ' alt="Klarna" width="70" style="display:block" />'),
                            align="center",
                            gap="24px",
                            theme="default",
                        ),
                        Text(
                            "We created a personal account for you. Please confirm your e-mail address and use our service to the maximum",
                            size="small",
                            tone="muted",
                            align="center",
                            theme="default",
                        ),
                        gap="36px",
                        align="center",
                        theme="default",
                    ),
                    padding="44px 24px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Section(
                ui.Stack(
                    ui.Heading(
                        "Supported payment services",
                        level="small",
                        align="center",
                        styles={"font-size": "20px", "line-height": "1.4"},
                        theme="default",
                    ),
                    ui.Inline(
                        curated_logo_markup("Stripe", 57, "#635bff", "#ffffff"),
                        curated_logo_markup("Apple Pay", 60, "#111827", "#ffffff"),
                        curated_logo_markup("Mastercard", 40, "#fff7ed", "#c2410c"),
                        curated_logo_markup("Visa", 50, "#eff6ff", "#1d4ed8"),
                        curated_logo_markup("Klarna", 70, "#fce7f3", "#9d174d"),
                        align="center",
                        gap="24px",
                        theme="default",
                    ),
                    ui.Text(
                        "We created a personal account for you. Please confirm your e-mail address and use our service to the maximum",
                        size="small",
                        tone="muted",
                        align="center",
                        styles={"max-width": "420px", "margin": "0 auto"},
                        theme="default",
                    ),
                    gap="36px",
                    align="center",
                    theme="default",
                ),
                padding="44px 24px",
                theme="default",
            ),
        ),
        spec(
            category="HERO",
            title="HERO block overlay",
            slug="hero-block-overlay",
            description="An image-backed hero using nested surfaces instead of raw HTML.",
            code=dedent(
                """
                from pyzahidal import Button, EmailDocument, Footer, Header, Heading, Inline, MenuItemSpec, SocialLinkSpec, Stack, Surface, Text

                email = EmailDocument(
                    title="SumUp launch update",
                    preview_text="Transaction fees as low as 0.89% for modern entrepreneurs.",
                    theme="modern",
                    sections=[
                        Header(
                            "SumUp",
                            [
                                MenuItemSpec("Products", href="#products"),
                                MenuItemSpec("Pricing", href="#pricing"),
                                MenuItemSpec("Docs", href="#docs"),
                            ],
                            tagline="Powering modern entrepreneurs",
                            meta_label="Spring launch",
                            theme="modern",
                        ),
                        Surface(
                            Surface(
                                Stack(
                                    Text("Transaction fees as low as 0.89%", size="kicker", tone="inverse"),
                                    Heading("SumUp", level="hero", tone="inverse"),
                                    Text("Powering modern entrepreneurs", tone="inverse"),
                                    Inline(Button("Discover how", href="#")),
                                    gap="18px",
                                ),
                                tone="overlay",
                                padding="44px",
                                radius="18px",
                            ),
                            background_image="https://images.example.com/sumup-hero.jpg",
                            background_color="#0f172a",
                            padding="36px",
                            radius="24px",
                        ),
                        Surface(
                            Stack(
                                Text("Why teams switch", size="kicker"),
                                Heading("Built to launch faster and iterate with less HTML debt.", level="small"),
                                Text(
                                    "Compose hero sections, follow-up content, and calls to action in Python while keeping the final output email-client friendly.",
                                ),
                                gap="12px",
                            ),
                            padding="28px",
                        ),
                        Footer(
                            "SumUp",
                            [
                                SocialLinkSpec(label="X", href="#x"),
                                SocialLinkSpec(label="LinkedIn", href="#linkedin"),
                                SocialLinkSpec(label="GitHub", href="#github"),
                            ],
                            description="Launch faster with reusable email sections, cleaner defaults, and branded flows that still stay easy to iterate.",
                            menu_items=[
                                MenuItemSpec("Platform", href="#platform"),
                                MenuItemSpec("Pricing", href="#pricing"),
                                MenuItemSpec("Support", href="#support"),
                            ],
                            legal_links=[
                                MenuItemSpec("Privacy", href="#privacy"),
                                MenuItemSpec("Terms", href="#terms"),
                            ],
                            disclaimer="You are receiving this product update because you asked for launch news from SumUp.",
                            theme="modern",
                        ),
                    ],
                )
                """
            ),
            factory=lambda: ui.EmailDocument(
                title="SumUp launch update",
                preview_text="Transaction fees as low as 0.89% for modern entrepreneurs.",
                theme="modern",
                sections=[
                    ui.Header(
                        "SumUp",
                        [
                            ui.MenuItemSpec("Products", href="#products"),
                            ui.MenuItemSpec("Pricing", href="#pricing"),
                            ui.MenuItemSpec("Docs", href="#docs"),
                        ],
                        tagline="Powering modern entrepreneurs",
                        meta_label="Spring launch",
                        theme="modern",
                    ),
                    ui.Surface(
                        ui.Surface(
                            ui.Stack(
                                ui.Text("Transaction fees as low as 0.89%", size="kicker", tone="inverse"),
                                ui.Heading("SumUp", level="hero", tone="inverse"),
                                ui.Text("Powering modern entrepreneurs", tone="inverse"),
                                ui.Inline(ui.Button("Discover how", href="#")),
                                gap="18px",
                            ),
                            tone="overlay",
                            padding="44px",
                            radius="18px",
                        ),
                        background_image="https://images.example.com/sumup-hero.jpg",
                        background_color="#0f172a",
                        padding="36px",
                        radius="24px",
                    ),
                    ui.Surface(
                        ui.Stack(
                            ui.Text("Why teams switch", size="kicker"),
                            ui.Heading("Built to launch faster and iterate with less HTML debt.", level="small"),
                            ui.Text(
                                "Compose hero sections, follow-up content, and calls to action in Python while keeping the final output email-client friendly.",
                            ),
                            gap="12px",
                        ),
                        padding="28px",
                    ),
                    ui.Footer(
                        "SumUp",
                        [
                            ui.SocialLinkSpec(label="X", href="#x"),
                            ui.SocialLinkSpec(label="LinkedIn", href="#linkedin"),
                            ui.SocialLinkSpec(label="GitHub", href="#github"),
                        ],
                        description="Launch faster with reusable email sections, cleaner defaults, and branded flows that still stay easy to iterate.",
                        menu_items=[
                            ui.MenuItemSpec("Platform", href="#platform"),
                            ui.MenuItemSpec("Pricing", href="#pricing"),
                            ui.MenuItemSpec("Support", href="#support"),
                        ],
                        legal_links=[
                            ui.MenuItemSpec("Privacy", href="#privacy"),
                            ui.MenuItemSpec("Terms", href="#terms"),
                        ],
                        disclaimer="You are receiving this product update because you asked for launch news from SumUp.",
                        theme="modern",
                    ),
                ],
            ),
            theme="modern",
        ),
        spec(
            category="Coupons",
            title="Card coupons",
            slug="coupons-card-coupons",
            description="A centered coupon card with a high-contrast redeem action.",
            code=dedent(
                """
                from pyzahidal import Button, Coupon, Stack, Text

                component = Stack(
                    Coupon("WINTER20OFF", "Use this code at checkout to unlock the extra savings.", theme="vibrant"),
                    Text("Valid through Friday midnight.", size="small", tone="muted", align="center", theme="vibrant"),
                    Button("Shop now", href="#", theme="vibrant"),
                    gap="16px",
                    align="center",
                    theme="vibrant",
                )
                """
            ),
            factory=lambda: ui.Stack(
                ui.Coupon("WINTER20OFF", "Use this code at checkout to unlock the extra savings.", theme="vibrant"),
                ui.Text("Valid through Friday midnight.", size="small", tone="muted", align="center", theme="vibrant"),
                ui.Button("Shop now", href="#", theme="vibrant"),
                gap="16px",
                align="center",
                theme="vibrant",
            ),
            theme="vibrant",
        ),
        spec(
            category="Call to Action",
            title="CTA with background image",
            slug="cta-with-background-image",
            description="A boxed CTA that uses token-driven overlay surfaces on top of imagery.",
            code=dedent(
                """
                from pyzahidal import Button, Heading, Inline, Stack, Surface, Text

                component = Surface(
                    Surface(
                        Stack(
                            Heading("Your upgrade starts here!", level="section", tone="inverse", align="center", theme="modern"),
                            Text(
                                "Step into the next generation of innovation with pro-level performance and cleaner workflows.",
                                tone="inverse",
                                align="center",
                                theme="modern",
                            ),
                            Inline(
                                Button("Sign up now", href="#", theme="modern"),
                                Button("Discover more", href="#", variant="ghost", styles={"color": "#ffffff", "border": "1px solid #ffffff"}, theme="modern"),
                                align="center",
                                gap="16px",
                                theme="modern",
                            ),
                            gap="20px",
                            theme="modern",
                        ),
                        tone="overlay",
                        padding="56px 44px",
                        radius="12px",
                        theme="modern",
                    ),
                    background_image="https://images.example.com/upgrade.jpg",
                    background_color="#1f2937",
                    padding="30px",
                    radius="24px",
                    theme="modern",
                )
                """
            ),
            factory=lambda: ui.Surface(
                ui.Surface(
                    ui.Stack(
                        ui.Heading("Your upgrade starts here!", level="section", tone="inverse", align="center", theme="modern"),
                        ui.Text(
                            "Step into the next generation of innovation with pro-level performance and cleaner workflows.",
                            tone="inverse",
                            align="center",
                            theme="modern",
                        ),
                        ui.Inline(
                            ui.Button("Sign up now", href="#", theme="modern"),
                            ui.Button("Discover more", href="#", variant="ghost", styles={"color": "#ffffff", "border": "1px solid #ffffff"}, theme="modern"),
                            align="center",
                            gap="16px",
                            theme="modern",
                        ),
                        gap="20px",
                        theme="modern",
                    ),
                    tone="overlay",
                    padding="56px 44px",
                    radius="12px",
                    theme="modern",
                ),
                background_image="https://images.example.com/upgrade.jpg",
                background_color="#1f2937",
                padding="30px",
                radius="24px",
                theme="modern",
            ),
            theme="modern",
        ),
        spec(
            category="Bento grids",
            title="Bento grid with images and details",
            slug="bento-grid-with-images-and-details",
            description="A highlight grid using the library's bento section instead of exported markup.",
            code=dedent(
                """
                from pyzahidal import BentoGrid
                from pyzahidal.base import BentoItemSpec

                component = BentoGrid(
                    [
                        BentoItemSpec("Live dashboards", "Watch campaign performance update in real time.", eyebrow="Analytics"),
                        BentoItemSpec("Flow control", "Branch onboarding and lifecycle sends from one place.", eyebrow="Automation"),
                        BentoItemSpec("Audience cards", "Combine CRM context with message-ready layouts.", eyebrow="Personalization"),
                    ],
                    theme="modern",
                )
                """
            ),
            factory=lambda: ui.BentoGrid(
                [
                    ui.BentoItemSpec("Live dashboards", "Watch campaign performance update in real time.", eyebrow="Analytics"),
                    ui.BentoItemSpec("Flow control", "Branch onboarding and lifecycle sends from one place.", eyebrow="Automation"),
                    ui.BentoItemSpec("Audience cards", "Combine CRM context with message-ready layouts.", eyebrow="Personalization"),
                ],
                theme="modern",
            ),
            theme="modern",
        ),
        spec(
            category="Footers",
            title="Footer with top background image and content bottom",
            slug="footer-with-top-background-image-and-content-bottom",
            description="A rich footer assembled from existing footer, menu, and social primitives.",
            code=dedent(
                """
                from pyzahidal import Footer, SocialLinkSpec

                component = Footer(
                    "Acme Studio",
                    [SocialLinkSpec(href="#x", label="X"), SocialLinkSpec(href="#linkedin", label="LinkedIn"), SocialLinkSpec(href="#github", label="GitHub")],
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Footer(
                "Acme Studio",
                [
                    ui.SocialLinkSpec(href="#x", label="X"),
                    ui.SocialLinkSpec(href="#linkedin", label="LinkedIn"),
                    ui.SocialLinkSpec(href="#github", label="GitHub"),
                ],
                theme="default",
            ),
        ),
        spec(
            category="Headers",
            title="Header with logo and menu",
            slug="header-with-logo-and-menu",
            description="A compact header using the high-level `Header` section.",
            code=dedent(
                """
                from pyzahidal import Header, MenuItemSpec

                component = Header(
                    "Acme Studio",
                    [MenuItemSpec("Products", href="#products"), MenuItemSpec("Pricing", href="#pricing"), MenuItemSpec("Docs", href="#docs")],
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Header(
                "Acme Studio",
                [
                    ui.MenuItemSpec("Products", href="#products"),
                    ui.MenuItemSpec("Pricing", href="#pricing"),
                    ui.MenuItemSpec("Docs", href="#docs"),
                ],
                theme="default",
            ),
        ),
        spec(
            category="Feature",
            title="Feature with double tall background images",
            slug="feature-with-double-tall-background-images",
            description="A split spotlight that combines copy and image-backed surfaces.",
            code=dedent(
                """
                from pyzahidal import Columns, Heading, Surface, Text

                component = Columns(
                    Surface(
                        Heading("Focused execution", level="small", theme="modern"),
                        Text("Track launches, automate follow-ups, and keep every team aligned in one workflow.", theme="modern"),
                        padding="24px",
                        theme="modern",
                    ),
                    Surface("", background_image="https://images.example.com/feature-panel.jpg", background_color="#dbeafe", padding="180px 0", theme="modern"),
                    widths=["48%", "52%"],
                    gap="18px",
                )
                """
            ),
            factory=lambda: ui.Columns(
                ui.Surface(
                    ui.Heading("Focused execution", level="small", theme="modern"),
                    ui.Text("Track launches, automate follow-ups, and keep every team aligned in one workflow.", theme="modern"),
                    padding="24px",
                    theme="modern",
                ),
                ui.Surface("", background_image="https://images.example.com/feature-panel.jpg", background_color="#dbeafe", padding="180px 0", theme="modern"),
                widths=["48%", "52%"],
                gap="18px",
            ),
            theme="modern",
        ),
        spec(
            category="Images",
            title="Full width image",
            slug="images-full-width-image",
            description="A single framed image preview built with the `Image` primitive.",
            code='from pyzahidal import Image\n\ncomponent = Image("https://images.example.com/showcase.jpg", alt="Showcase", theme="editorial")',
            factory=lambda: ui.Image("https://images.example.com/showcase.jpg", alt="Showcase", theme="editorial"),
            theme="editorial",
        ),
        spec(
            category="Stats",
            title="Simple stats",
            slug="stats-simple-stats",
            description="A simple metrics block rendered through the reusable `Stats` section.",
            code=dedent(
                """
                from pyzahidal import MetricSpec, Stats

                component = Stats(
                    [
                        MetricSpec(label="Revenue", value="$48k", detail="Monthly recurring"),
                        MetricSpec(label="Open rate", value="58%", detail="Across launch sends"),
                        MetricSpec(label="CTR", value="9.1%", detail="From primary CTAs"),
                    ],
                    theme="vibrant",
                )
                """
            ),
            factory=lambda: ui.Stats(
                [
                    _metric_spec("Revenue", "$48k", "Monthly recurring"),
                    _metric_spec("Open rate", "58%", "Across launch sends"),
                    _metric_spec("CTR", "9.1%", "From primary CTAs"),
                ],
                theme="vibrant",
            ),
            theme="vibrant",
        ),
        spec(
            category="Social",
            title="Simple social logos row",
            slug="social-simple-social-logos-row",
            description="A social follow row using the built-in icon link treatment.",
            code=dedent(
                """
                from pyzahidal import SocialLinkSpec, SocialLinks

                component = SocialLinks(
                    [
                        SocialLinkSpec(href="#x", icon_src="https://images.example.com/x.png", alt="X"),
                        SocialLinkSpec(href="#linkedin", icon_src="https://images.example.com/linkedin.png", alt="LinkedIn"),
                        SocialLinkSpec(href="#github", icon_src="https://images.example.com/github.png", alt="GitHub"),
                    ],
                    mode="icon",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.SocialLinks(
                [
                    _social_link_spec(href="#x", icon_src="https://images.example.com/x.png", alt="X"),
                    _social_link_spec(href="#linkedin", icon_src="https://images.example.com/linkedin.png", alt="LinkedIn"),
                    _social_link_spec(href="#github", icon_src="https://images.example.com/github.png", alt="GitHub"),
                ],
                mode="icon",
                theme="default",
            ),
        ),
        spec(
            category="Blog",
            title="2 columns blog with images",
            slug="blog-2-columns-blog-with-images",
            description="A two-card editorial layout built from rows, images, and copy blocks.",
            code=dedent(
                """
                from pyzahidal import Button, Columns, EmailDocument, Footer, Header, Heading, Image, MenuItemSpec, SocialLinkSpec, Stack, Surface, Text

                email = EmailDocument(
                    title="Acme editorial digest",
                    preview_text="Two stories on email design systems and calmer launch recaps.",
                    theme="editorial",
                    sections=[
                        Header(
                            "Acme Weekly",
                            [
                                MenuItemSpec("Stories", href="#stories"),
                                MenuItemSpec("Archive", href="#archive"),
                                MenuItemSpec("About", href="#about"),
                            ],
                            tagline="Notes for design, growth, and lifecycle teams",
                            meta_label="Issue 042",
                            theme="editorial",
                        ),
                        Surface(
                            Stack(
                                Text("Weekly digest", size="kicker"),
                                Heading("Notes from the email desk", level="hero"),
                                Text(
                                    "A curated readout for design, growth, and lifecycle teams shipping customer communication every week.",
                                ),
                                gap="12px",
                            ),
                            padding="28px",
                        ),
                        Columns(
                            Surface(
                                Stack(
                                    Image("https://images.example.com/post-one.jpg", alt="Post one"),
                                    Heading("Design systems for email", level="small"),
                                    Text("How to keep layouts consistent without giving up flexibility."),
                                    Button("Read more", href="#"),
                                    gap="12px",
                                ),
                                padding="18px",
                            ),
                            Surface(
                                Stack(
                                    Image("https://images.example.com/post-two.jpg", alt="Post two"),
                                    Heading("Better launch recaps", level="small"),
                                    Text("A calmer postmortem format for product, growth, and design teams."),
                                    Button("Read more", href="#"),
                                    gap="12px",
                                ),
                                padding="18px",
                            ),
                            gap="18px",
                        ),
                        Footer(
                            "Acme Weekly",
                            [
                                SocialLinkSpec(label="X", href="#x"),
                                SocialLinkSpec(label="LinkedIn", href="#linkedin"),
                                SocialLinkSpec(label="RSS", href="#rss"),
                            ],
                            description="A calmer editorial digest for teams building email systems, launch recaps, and repeatable communication.",
                            menu_items=[
                                MenuItemSpec("Archive", href="#archive"),
                                MenuItemSpec("Preferences", href="#preferences"),
                                MenuItemSpec("Advertise", href="#advertise"),
                            ],
                            legal_links=[
                                MenuItemSpec("Unsubscribe", href="#unsubscribe"),
                                MenuItemSpec("Manage email", href="#manage"),
                            ],
                            disclaimer="You are receiving this digest because you subscribed to editorial updates from Acme Weekly.",
                            theme="editorial",
                        ),
                    ],
                )
                """
            ),
            factory=lambda: ui.EmailDocument(
                title="Acme editorial digest",
                preview_text="Two stories on email design systems and calmer launch recaps.",
                theme="editorial",
                sections=[
                    ui.Header(
                        "Acme Weekly",
                        [
                            ui.MenuItemSpec("Stories", href="#stories"),
                            ui.MenuItemSpec("Archive", href="#archive"),
                            ui.MenuItemSpec("About", href="#about"),
                        ],
                        tagline="Notes for design, growth, and lifecycle teams",
                        meta_label="Issue 042",
                        theme="editorial",
                    ),
                    ui.Surface(
                        ui.Stack(
                            ui.Text("Weekly digest", size="kicker"),
                            ui.Heading("Notes from the email desk", level="hero"),
                            ui.Text(
                                "A curated readout for design, growth, and lifecycle teams shipping customer communication every week.",
                            ),
                            gap="12px",
                        ),
                        padding="28px",
                    ),
                    ui.Columns(
                        ui.Surface(
                            ui.Stack(
                                ui.Image("https://images.example.com/post-one.jpg", alt="Post one"),
                                ui.Heading("Design systems for email", level="small"),
                                ui.Text("How to keep layouts consistent without giving up flexibility."),
                                ui.Button("Read more", href="#"),
                                gap="12px",
                            ),
                            padding="18px",
                        ),
                        ui.Surface(
                            ui.Stack(
                                ui.Image("https://images.example.com/post-two.jpg", alt="Post two"),
                                ui.Heading("Better launch recaps", level="small"),
                                ui.Text("A calmer postmortem format for product, growth, and design teams."),
                                ui.Button("Read more", href="#"),
                                gap="12px",
                            ),
                            padding="18px",
                        ),
                        gap="18px",
                    ),
                    ui.Footer(
                        "Acme Weekly",
                        [
                            ui.SocialLinkSpec(label="X", href="#x"),
                            ui.SocialLinkSpec(label="LinkedIn", href="#linkedin"),
                            ui.SocialLinkSpec(label="RSS", href="#rss"),
                        ],
                        description="A calmer editorial digest for teams building email systems, launch recaps, and repeatable communication.",
                        menu_items=[
                            ui.MenuItemSpec("Archive", href="#archive"),
                            ui.MenuItemSpec("Preferences", href="#preferences"),
                            ui.MenuItemSpec("Advertise", href="#advertise"),
                        ],
                        legal_links=[
                            ui.MenuItemSpec("Unsubscribe", href="#unsubscribe"),
                            ui.MenuItemSpec("Manage email", href="#manage"),
                        ],
                        disclaimer="You are receiving this digest because you subscribed to editorial updates from Acme Weekly.",
                        theme="editorial",
                    ),
                ],
            ),
            theme="editorial",
        ),
        spec(
            category="Content",
            title="Title with regular padding",
            slug="content-title-with-regular-padding",
            description="A straightforward content section with typography-driven hierarchy.",
            code=dedent(
                """
                from pyzahidal import Heading, Section, Stack, Text

                component = Section(
                    Stack(
                        Text("Product notes", size="kicker", theme="editorial"),
                        Heading("Designing with fewer one-off variants", level="section", theme="editorial"),
                        Text("Build from primitives, extend the tokens you need, and keep the docs examples readable.", theme="editorial"),
                        gap="12px",
                        theme="editorial",
                    ),
                    theme="editorial",
                )
                """
            ),
            factory=lambda: ui.Section(
                ui.Stack(
                    ui.Text("Product notes", size="kicker", theme="editorial"),
                    ui.Heading("Designing with fewer one-off variants", level="section", theme="editorial"),
                    ui.Text("Build from primitives, extend the tokens you need, and keep the docs examples readable.", theme="editorial"),
                    gap="12px",
                    theme="editorial",
                ),
                theme="editorial",
            ),
            theme="editorial",
        ),
        spec(
            category="FAQs",
            title="Expanded FAQ with numbers",
            slug="faq-expanded-faq-with-numbers",
            description="An expanded FAQ rendered from the reusable FAQ section.",
            code=dedent(
                """
                from pyzahidal import FAQ, FaqItemSpec

                component = FAQ(
                    [
                        FaqItemSpec("Can we use Jinja placeholders?", "Yes. Use raw() only for template placeholders, not for layout markup."),
                        FaqItemSpec("Can we override tokens?", "Yes. Every themed component accepts theme_overrides for targeted adjustments."),
                    ],
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.FAQ(
                [
                    _faq_spec("Can we use Jinja placeholders?", "Yes. Use raw() only for template placeholders, not for layout markup."),
                    _faq_spec("Can we override tokens?", "Yes. Every themed component accepts theme_overrides for targeted adjustments."),
                ],
                theme="default",
            ),
        ),
        spec(
            category="Team",
            title="2 column team cards",
            slug="team-2-column-team-cards",
            description="A team showcase using avatars, names, and roles in card surfaces.",
            code=dedent(
                """
                from pyzahidal import Team, TeamMemberSpec

                component = Team(
                    [
                        TeamMemberSpec(name="Avery Chen", role="Product Design", image="https://images.example.com/avery.png"),
                        TeamMemberSpec(name="Nina Sol", role="Lifecycle Marketing", image="https://images.example.com/nina.png"),
                    ],
                    theme="editorial",
                )
                """
            ),
            factory=lambda: ui.Team(
                [
                    ui.TeamMemberSpec(name="Avery Chen", role="Product Design", image="https://images.example.com/avery.png"),
                    ui.TeamMemberSpec(name="Nina Sol", role="Lifecycle Marketing", image="https://images.example.com/nina.png"),
                ],
                theme="editorial",
            ),
            theme="editorial",
        ),
        spec(
            category="Testimonials",
            title="Centered testimonial with CTA",
            slug="testimonials-centered-testimonial-with-cta",
            description="A centered proof block with an action anchored underneath.",
            code=dedent(
                """
                from pyzahidal import Button, Heading, Stack, Surface, Text

                component = Surface(
                    Stack(
                        Heading('"Our activation campaigns feel composed instead of improvised."', level="small", align="center", theme="editorial"),
                        Text("Avery Chen, Product Design", align="center", tone="muted", theme="editorial"),
                        Button("Read the case study", href="#", theme="editorial"),
                        gap="14px",
                        align="center",
                        theme="editorial",
                    ),
                    padding="28px",
                    theme="editorial",
                )
                """
            ),
            factory=lambda: ui.Surface(
                ui.Stack(
                    ui.Heading('"Our activation campaigns feel composed instead of improvised."', level="small", align="center", theme="editorial"),
                    ui.Text("Avery Chen, Product Design", align="center", tone="muted", theme="editorial"),
                    ui.Button("Read the case study", href="#", theme="editorial"),
                    gap="14px",
                    align="center",
                    theme="editorial",
                ),
                padding="28px",
                theme="editorial",
            ),
            theme="editorial",
        ),
        spec(
            category="Timelines",
            title="Stacked timeline",
            slug="timelines-stacked-timeline",
            description="A vertical rollout timeline using numbered cards.",
            code=dedent(
                """
                from pyzahidal import Timeline, TimelineStepSpec

                component = Timeline(
                    [
                        TimelineStepSpec("v1.0.0", "19 Jan", "Design", "Design", "Lock examples and signatures."),
                        TimelineStepSpec("v1.1.0", "20 Jan", "Build", "Build", "Generate previews and static pages."),
                        TimelineStepSpec("v1.2.0", "21 Jan", "Ship", "Ship", "Capture screenshots and publish docs."),
                    ],
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Timeline(
                [
                    _timeline_step_spec("v1.0.0", "19 Jan", "Design", "Design", "Lock examples and signatures."),
                    _timeline_step_spec("v1.1.0", "20 Jan", "Build", "Build", "Generate previews and static pages."),
                    _timeline_step_spec("v1.2.0", "21 Jan", "Ship", "Ship", "Capture screenshots and publish docs."),
                ],
                theme="default",
            ),
        ),
        spec(
            category="Pricing",
            title="Full width single pricing",
            slug="pricing-full-width-single-pricing",
            description="A featured commerce plan built from the reusable pricing section.",
            code=dedent(
                """
                from pyzahidal import ActionSpec, Pricing, PricingPlanSpec

                component = Pricing(
                    [
                        PricingPlanSpec("Scale", "$29", "Growth-ready sending for teams and campaigns.", badge="Popular", featured=True, features=["Unlimited emails", "Team seats", "Priority support"], action=ActionSpec("Choose plan", href="#", variant="primary"))
                    ],
                    theme="commerce",
                )
                """
            ),
            factory=lambda: ui.Pricing(
                [
                    ui.PricingPlanSpec("Scale", "$29", "Growth-ready sending for teams and campaigns.", badge="Popular", featured=True, features=["Unlimited emails", "Team seats", "Priority support"], action=_action_spec("Choose plan", href="#", variant="primary"))
                ],
                theme="commerce",
            ),
            theme="commerce",
        ),
        spec(
            category="Product Lists",
            title="Product list with rows",
            slug="product-list-with-rows",
            description="A simple ecommerce row list using the `ProductList` section.",
            code=dedent(
                """
                from pyzahidal import ProductList, ProductSpec

                component = ProductList(
                    [
                        ProductSpec("Desk Lamp", "$49", "Warm light for focused work.", href="#"),
                        ProductSpec("Monitor Arm", "$89", "Free up desk space with a cleaner setup.", href="#"),
                    ],
                    theme="commerce",
                )
                """
            ),
            factory=lambda: ui.ProductList(
                [
                    ui.ProductSpec("Desk Lamp", "$49", "Warm light for focused work.", href="#"),
                    ui.ProductSpec("Monitor Arm", "$89", "Free up desk space with a cleaner setup.", href="#"),
                ],
                theme="commerce",
            ),
            theme="commerce",
        ),
        spec(
            category="Product Detail",
            title="Split product detail",
            slug="split-product-detail",
            description="A focused single-product feature using the library's detail section.",
            code=dedent(
                """
                from pyzahidal import ProductDetail

                component = ProductDetail(
                    "Toothpaste Salt",
                    "$12.99",
                    "A cleaner nightly routine with mineral-rich ingredients and a calmer flavor profile.",
                    "https://images.example.com/toothpaste.jpg",
                    theme="commerce",
                )
                """
            ),
            factory=lambda: ui.ProductDetail(
                "Toothpaste Salt",
                "$12.99",
                "A cleaner nightly routine with mineral-rich ingredients and a calmer flavor profile.",
                "https://images.example.com/toothpaste.jpg",
                theme="commerce",
            ),
            theme="commerce",
        ),
        spec(
            category="Category Previews",
            title="Category preview with cards",
            slug="category-preview-with-cards",
            description="A category picker that highlights shoppable groupings.",
            code=dedent(
                """
                from pyzahidal import CategoryPreview

                component = CategoryPreview(
                    "Shop by room",
                    [("Desk", "#desk"), ("Bedroom", "#bedroom"), ("Studio", "#studio"), ("Outdoor", "#outdoor")],
                    theme="commerce",
                )
                """
            ),
            factory=lambda: ui.CategoryPreview(
                "Shop by room",
                [("Desk", "#desk"), ("Bedroom", "#bedroom"), ("Studio", "#studio"), ("Outdoor", "#outdoor")],
                theme="commerce",
            ),
            theme="commerce",
        ),
        spec(
            category="Shopping Cart",
            title="Shopping cart with row items",
            slug="shopping-cart-with-row-items",
            description="A cart summary rendered through the shopping cart section.",
            code=dedent(
                """
                from pyzahidal import CartItemSpec, ShoppingCart

                component = ShoppingCart(
                    [
                        CartItemSpec("Desk Lamp", "1", "$49"),
                        CartItemSpec("Bulb pack", "2", "$18"),
                    ],
                    theme="commerce",
                )
                """
            ),
            factory=lambda: ui.ShoppingCart(
                [
                    ui.CartItemSpec("Desk Lamp", "1", "$49"),
                    ui.CartItemSpec("Bulb pack", "2", "$18"),
                ],
                theme="commerce",
            ),
            theme="commerce",
        ),
        spec(
            category="Reviews",
            title="Full width reviews",
            slug="reviews-full-width-reviews",
            description="A reviews block rendered through the shared testimonials-style API.",
            code=dedent(
                """
                from pyzahidal import ReviewSpec, Reviews

                component = Reviews(
                    [
                        ReviewSpec(quote="Warm light, small footprint, and the unboxing felt premium.", author="Mia P."),
                        ReviewSpec(quote="Easy to gift and easy to reorder when we refresh our studio setup.", author="Jon H."),
                    ],
                    theme="editorial",
                )
                """
            ),
            factory=lambda: ui.Reviews(
                [
                    ui.ReviewSpec(quote="Warm light, small footprint, and the unboxing felt premium.", author="Mia P."),
                    ui.ReviewSpec(quote="Easy to gift and easy to reorder when we refresh our studio setup.", author="Jon H."),
                ],
                theme="editorial",
            ),
            theme="editorial",
        ),
        spec(
            category="Order Summary",
            title="Boxed order summary with card details and total bottom",
            slug="boxed-order-summary-with-card-details-and-total-bottom",
            description="A transactional summary using the reusable order summary section.",
            code=dedent(
                """
                from pyzahidal import Button, EmailDocument, Footer, Header, Heading, MenuItemSpec, OrderSummary, SocialLinkSpec, Stack, Surface, Text

                email = EmailDocument(
                    title="Order confirmation",
                    preview_text="Your order is confirmed and fulfillment is already underway.",
                    theme="commerce",
                    sections=[
                        Header(
                            "Acme Store",
                            [
                                MenuItemSpec("Track order", href="#track"),
                                MenuItemSpec("Support", href="#support"),
                            ],
                            tagline="Order #1042",
                            meta_label="Help center",
                            theme="commerce",
                        ),
                        Surface(
                            Stack(
                                Text("Order confirmed", size="kicker"),
                                Heading("Thanks for shopping with Acme", level="hero"),
                                Text(
                                    "We have received your order and started preparing it for shipment. Here is the latest summary before it heads out.",
                                ),
                                gap="12px",
                            ),
                            padding="28px",
                        ),
                        OrderSummary(
                            [("Subtotal", "$40"), ("Shipping", "$5"), ("Total", "$45")],
                            progress=75,
                        ),
                        Surface(
                            Stack(
                                Text("Need anything before it ships?", size="small", tone="muted"),
                                Button("View order details", href="#"),
                                gap="12px",
                            ),
                            padding="24px",
                        ),
                        Footer(
                            "Acme Store",
                            [
                                SocialLinkSpec(label="Support", href="#support"),
                                SocialLinkSpec(label="Orders", href="#orders"),
                            ],
                            description="Need to make a change? Review your order details, delivery updates, and support options in one place.",
                            menu_items=[
                                MenuItemSpec("Help center", href="#help"),
                                MenuItemSpec("Shipping", href="#shipping"),
                                MenuItemSpec("Returns", href="#returns"),
                            ],
                            legal_links=[
                                MenuItemSpec("Manage order", href="#manage-order"),
                                MenuItemSpec("Privacy", href="#privacy"),
                            ],
                            disclaimer="This transactional email was sent because you placed an order with Acme Store.",
                            theme="commerce",
                        ),
                    ],
                )
                """
            ),
            factory=lambda: ui.EmailDocument(
                title="Order confirmation",
                preview_text="Your order is confirmed and fulfillment is already underway.",
                theme="commerce",
                sections=[
                    ui.Header(
                        "Acme Store",
                        [
                            ui.MenuItemSpec("Track order", href="#track"),
                            ui.MenuItemSpec("Support", href="#support"),
                        ],
                        tagline="Order #1042",
                        meta_label="Help center",
                        theme="commerce",
                    ),
                    ui.Surface(
                        ui.Stack(
                            ui.Text("Order confirmed", size="kicker"),
                            ui.Heading("Thanks for shopping with Acme", level="hero"),
                            ui.Text(
                                "We have received your order and started preparing it for shipment. Here is the latest summary before it heads out.",
                            ),
                            gap="12px",
                        ),
                        padding="28px",
                    ),
                    ui.OrderSummary(
                        [("Subtotal", "$40"), ("Shipping", "$5"), ("Total", "$45")],
                        progress=75,
                    ),
                    ui.Surface(
                        ui.Stack(
                            ui.Text("Need anything before it ships?", size="small", tone="muted"),
                            ui.Button("View order details", href="#"),
                            gap="12px",
                        ),
                        padding="24px",
                    ),
                    ui.Footer(
                        "Acme Store",
                        [
                            ui.SocialLinkSpec(label="Support", href="#support"),
                            ui.SocialLinkSpec(label="Orders", href="#orders"),
                        ],
                        description="Need to make a change? Review your order details, delivery updates, and support options in one place.",
                        menu_items=[
                            ui.MenuItemSpec("Help center", href="#help"),
                            ui.MenuItemSpec("Shipping", href="#shipping"),
                            ui.MenuItemSpec("Returns", href="#returns"),
                        ],
                        legal_links=[
                            ui.MenuItemSpec("Manage order", href="#manage-order"),
                            ui.MenuItemSpec("Privacy", href="#privacy"),
                        ],
                        disclaimer="This transactional email was sent because you placed an order with Acme Store.",
                        theme="commerce",
                    ),
                ],
            ),
            theme="commerce",
        ),
        spec(
            category="Containers",
            title="Container flush on mobile",
            slug="container-flush-on-mobile",
            description="A minimal panel container for wrapped messaging.",
            code=dedent(
                """
                from pyzahidal import Container, Stack, Text

                component = Container(
                    Stack(
                        Text("Container flush on mobile", size="kicker", theme="default"),
                        Text("A reusable wrapper for grouped content and calmer spacing.", theme="default"),
                        gap="10px",
                        theme="default",
                    ),
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Container(
                ui.Stack(
                    ui.Text("Container flush on mobile", size="kicker", theme="default"),
                    ui.Text("A reusable wrapper for grouped content and calmer spacing.", theme="default"),
                    gap="10px",
                    theme="default",
                ),
                theme="default",
            ),
        ),
        spec(
            category="Grids",
            title="One column grid",
            slug="one-column-grid",
            description="A single-column card grid using the same surface building blocks as multi-column layouts.",
            code=dedent(
                """
                from pyzahidal import Heading, Stack, Surface, Text

                component = Surface(
                    Stack(
                        Heading("Launch checklist", level="small", theme="default"),
                        Text("Finalize copy, lock screenshots, and ship the generated docs with a single review pass.", theme="default"),
                        gap="10px",
                        theme="default",
                    ),
                    padding="20px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Surface(
                ui.Stack(
                    ui.Heading("Launch checklist", level="small", theme="default"),
                    ui.Text("Finalize copy, lock screenshots, and ship the generated docs with a single review pass.", theme="default"),
                    gap="10px",
                    theme="default",
                ),
                padding="20px",
                theme="default",
            ),
        ),
        spec(
            category="Spacing",
            title="Vertical spacer",
            slug="vertical-spacer",
            description="An explicit spacing example using the `Spacer` primitive.",
            code=dedent(
                """
                from pyzahidal import Spacer, Stack, Text

                component = Stack(
                    Text("Release notes", theme="default"),
                    Spacer("32px"),
                    Text("Billing update", theme="default"),
                    gap="0",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Stack(ui.Text("Release notes", theme="default"), ui.Spacer("32px"), ui.Text("Billing update", theme="default"), gap="0", theme="default"),
        ),
        spec(
            category="Buttons",
            title="Primary buttons",
            slug="primary-buttons",
            description="A prominent action group built from token-driven buttons.",
            code=dedent(
                """
                from pyzahidal import Button, Inline

                component = Inline(
                    Button("Start free trial", href="#", theme="default"),
                    Button("Read docs", href="#", variant="secondary", theme="default"),
                    gap="12px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Inline(
                ui.Button("Start free trial", href="#", theme="default"),
                ui.Button("Read docs", href="#", variant="secondary", theme="default"),
                gap="12px",
                theme="default",
            ),
        ),
        spec(
            category="Pills",
            title="Basic pills with status colors",
            slug="basic-pills-with-status-colors",
            description="Status pills now use shared theme tokens instead of ad hoc colors.",
            code=dedent(
                """
                from pyzahidal import Inline, Pill

                component = Inline(
                    Pill("Healthy", tone="success", theme="default"),
                    Pill("Churn risk", tone="warning", theme="default"),
                    Pill("At risk", tone="danger", theme="default"),
                    gap="10px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Inline(
                ui.Pill("Healthy", tone="success", theme="default"),
                ui.Pill("Churn risk", tone="warning", theme="default"),
                ui.Pill("At risk", tone="danger", theme="default"),
                gap="10px",
                theme="default",
            ),
        ),
        spec(
            category="Avatars",
            title="Avatar with details",
            slug="avatar-with-details",
            description="A person row combining the avatar primitive with supporting text.",
            code=dedent(
                """
                from pyzahidal import Avatar, Inline, Stack, Text

                component = Inline(
                    Avatar("https://images.example.com/avery.png", alt="Avery", size="56px"),
                    Stack(
                        Text("Avery Chen", theme="default"),
                        Text("Product Design", size="small", tone="muted", theme="default"),
                        gap="6px",
                        theme="default",
                    ),
                    gap="12px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Inline(
                ui.Avatar("https://images.example.com/avery.png", alt="Avery", size="56px"),
                ui.Stack(
                    ui.Text("Avery Chen", theme="default"),
                    ui.Text("Product Design", size="small", tone="muted", theme="default"),
                    gap="6px",
                    theme="default",
                ),
                gap="12px",
                theme="default",
            ),
        ),
        spec(
            category="Progress Bars",
            title="Full width progress bar",
            slug="full-width-progress-bar",
            description="A simple progress card using the core progress primitive.",
            code=dedent(
                """
                from pyzahidal import ProgressBar, Stack, Text

                component = Stack(
                    Text("Profile completion", theme="default"),
                    ProgressBar(72, theme="default"),
                    Text("72% complete", size="small", tone="muted", theme="default"),
                    gap="10px",
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.Stack(
                ui.Text("Profile completion", theme="default"),
                ui.ProgressBar(72, theme="default"),
                ui.Text("72% complete", size="small", tone="muted", theme="default"),
                gap="10px",
                theme="default",
            ),
        ),
        spec(
            category="Data Tables",
            title="Basic",
            slug="data-tables-basic",
            description="A schema-driven table with renderable cells and token-backed status pills.",
            code=dedent(
                """
                from pyzahidal import Button, DataColumnSpec, DataTable, Pill

                component = DataTable(
                    columns=[
                        DataColumnSpec("owner", "Owner"),
                        DataColumnSpec("segment", "Segment"),
                        DataColumnSpec("health", "Health"),
                        DataColumnSpec("action", "Action", align="right"),
                    ],
                    rows=[
                        {
                            "owner": "John Adams",
                            "segment": "SMB - Monthly Plan",
                            "health": Pill("At risk", tone="danger", theme="default"),
                            "action": Button("Edit", href="#", variant="ghost", theme="default"),
                        },
                        {
                            "owner": "Hannah Aldersson",
                            "segment": "Mid-Market Accounts",
                            "health": Pill("Healthy", tone="success", theme="default"),
                            "action": Button("Edit", href="#", variant="ghost", theme="default"),
                        },
                    ],
                    striped=True,
                    compact=True,
                    theme="default",
                )
                """
            ),
            factory=lambda: ui.DataTable(
                columns=[
                    ui.DataColumnSpec("owner", "Owner"),
                    ui.DataColumnSpec("segment", "Segment"),
                    ui.DataColumnSpec("health", "Health"),
                    ui.DataColumnSpec("action", "Action", align="right"),
                ],
                rows=[
                    {
                        "owner": "John Adams",
                        "segment": "SMB - Monthly Plan",
                        "health": ui.Pill("At risk", tone="danger", theme="default"),
                        "action": ui.Button("Edit", href="#", variant="ghost", theme="default"),
                    },
                    {
                        "owner": "Hannah Aldersson",
                        "segment": "Mid-Market Accounts",
                        "health": ui.Pill("Healthy", tone="success", theme="default"),
                        "action": ui.Button("Edit", href="#", variant="ghost", theme="default"),
                    },
                ],
                striped=True,
                compact=True,
                theme="default",
            ),
        ),
    ]


@dataclass(frozen=True)
class CuratedTarget:
    category: str
    theme: str | None = None


CURATED_TARGETS = [
    CuratedTarget("Logos"),
    CuratedTarget("HERO", theme="modern"),
    CuratedTarget("Coupons", theme="vibrant"),
    CuratedTarget("Call to Action", theme="modern"),
    CuratedTarget("Bento grids", theme="modern"),
    CuratedTarget("Footers"),
    CuratedTarget("Headers"),
    CuratedTarget("Feature", theme="modern"),
    CuratedTarget("Images", theme="editorial"),
    CuratedTarget("Stats", theme="vibrant"),
    CuratedTarget("Social"),
    CuratedTarget("Blog", theme="editorial"),
    CuratedTarget("Content", theme="editorial"),
    CuratedTarget("FAQs"),
    CuratedTarget("Team", theme="editorial"),
    CuratedTarget("Testimonials", theme="editorial"),
    CuratedTarget("Timelines"),
    CuratedTarget("Pricing", theme="commerce"),
    CuratedTarget("Product Lists", theme="commerce"),
    CuratedTarget("Product Detail", theme="commerce"),
    CuratedTarget("Category Previews", theme="commerce"),
    CuratedTarget("Shopping Cart", theme="commerce"),
    CuratedTarget("Reviews", theme="editorial"),
    CuratedTarget("Order Summary", theme="commerce"),
    CuratedTarget("Containers"),
    CuratedTarget("Grids"),
    CuratedTarget("Spacing"),
    CuratedTarget("Buttons"),
    CuratedTarget("Pills"),
    CuratedTarget("Avatars"),
    CuratedTarget("Progress Bars"),
    CuratedTarget("Data Tables"),
]


CURATED_ASSET_URL_RE = re.compile(r"https://assets\.[^/]+/images/[^\s\"')>]+")
CURATED_IMAGE_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
CURATED_LINK_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
CURATED_TR_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
CURATED_TH_RE = re.compile(r"<th\b[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)
CURATED_TD_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
CURATED_ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(\".*?\"|'.*?'|[^\s>]+)", re.DOTALL)
CURATED_ONE_PIXEL_PNG = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000A49444154789C6360000002000154A24F5A0000000049454E44AE426082"
)
CURATED_VERSION_RE = re.compile(r"\bv\d+(?:\.\d+){1,3}\b", re.IGNORECASE)
CURATED_DATE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\b")


def load_curated_section_map() -> dict[tuple[str, str], dict[str, object]]:
    if not CURATED_EXPORT.exists():
        return {}
    payload = json.loads(CURATED_EXPORT.read_text(encoding="utf-8"))
    section_map: dict[tuple[str, str], dict[str, object]] = {}
    for page in payload.get("pages", []):
        category = page.get("pageHeading", "")
        page_url = page.get("pageUrl", "")
        for section in page.get("sections", []):
            title = section.get("previewHeading") or section.get("heading") or section.get("slug", "")
            normalized = str(title).replace(" Preview", "").strip()
            key = (str(category), normalized)
            if key in section_map:
                continue
            section_map[key] = {
                "category": category,
                "title": normalized,
                "page_url": page_url,
                "section": section,
            }
    return section_map


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200d", " ")).strip()


def _strip_html(value: str) -> str:
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return _normalize_whitespace(unescape(text))


def _parse_attrs(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for name, value in CURATED_ATTR_RE.findall(tag):
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] in {"'", '"'} and cleaned[-1] == cleaned[0]:
            cleaned = cleaned[1:-1]
        attrs[name.lower()] = unescape(cleaned)
    return attrs


def _extract_tag_texts(html: str, tag: str) -> list[str]:
    pattern = re.compile(rf"<{tag}\b[^>]*>(.*?)</{tag}>", re.IGNORECASE | re.DOTALL)
    texts: list[str] = []
    for value in pattern.findall(html):
        cleaned = _strip_html(value)
        if cleaned and cleaned not in texts:
            texts.append(cleaned)
    return texts


def _extract_links(html: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for attrs_raw, body in CURATED_LINK_RE.findall(html):
        attrs = _parse_attrs(attrs_raw)
        href = attrs.get("href", "").strip()
        label = _strip_html(body)
        if not href:
            continue
        record = {"href": href, "label": label or href}
        if record not in links:
            links.append(record)
    return links


def _extract_images(html: str) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    for tag in CURATED_IMAGE_TAG_RE.findall(html):
        attrs = _parse_attrs(tag)
        src = attrs.get("src", "").strip()
        if not src:
            continue
        alt = attrs.get("alt", "").strip()
        record = {"src": src, "alt": alt}
        if record not in images:
            images.append(record)
    return images


def _extract_table_data(html: str) -> tuple[list[str], list[list[str]]]:
    parsed_rows: list[tuple[str, list[str]]] = []
    for row_html in CURATED_TR_RE.findall(html):
        headers = [_strip_html(cell) for cell in CURATED_TH_RE.findall(row_html)]
        headers = [cell for cell in headers if cell]
        if headers:
            parsed_rows.append(("header", headers))
            continue
        cells = [_strip_html(cell) for cell in CURATED_TD_RE.findall(row_html)]
        cells = [cell for cell in cells if cell]
        if cells:
            parsed_rows.append(("row", cells))
    header: list[str] = []
    rows: list[list[str]] = []
    for index, (kind, values) in enumerate(parsed_rows):
        if kind == "header" and len(values) >= 2:
            header = values
            for next_kind, next_values in parsed_rows[index + 1 :]:
                if next_kind != "row":
                    continue
                if len(next_values) >= len(header):
                    rows.append(next_values[: len(header)])
                if len(rows) >= 6:
                    break
            break
    if not header:
        candidates = [values for kind, values in parsed_rows if kind == "row" and len(values) >= 2]
        if candidates:
            header = candidates[0]
            rows = [row[: len(header)] for row in candidates[1:7]]
    return header, rows


def _curated_style_values(html: str, prop: str) -> list[str]:
    pattern = re.compile(rf"{re.escape(prop)}\s*:\s*([^;\"']+)", re.IGNORECASE)
    return [_normalize_whitespace(value) for value in pattern.findall(html) if _normalize_whitespace(value)]


def _curated_group_texts(headings: Sequence[str], paragraphs: Sequence[str]) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    paragraph_index = 0
    for index, heading in enumerate(headings):
        body: list[str] = []
        if paragraph_index < len(paragraphs):
            body.append(paragraphs[paragraph_index])
            paragraph_index += 1
        if index > 0 and paragraph_index < len(paragraphs) and len(body[0].split()) < 18:
            next_value = paragraphs[paragraph_index]
            if "$" in next_value or len(next_value.split()) < 16:
                body.append(next_value)
                paragraph_index += 1
        groups.append({"heading": heading, "paragraphs": body})
    if not groups and paragraphs:
        for paragraph in paragraphs:
            groups.append({"heading": "", "paragraphs": [paragraph]})
    return groups


def _curated_layout_flags(html: str, headings: Sequence[str], paragraphs: Sequence[str], images: Sequence[dict[str, str]], links: Sequence[dict[str, str]], table_headers: Sequence[str], table_rows: Sequence[Sequence[str]]) -> dict[str, object]:
    text_align_center_count = len(re.findall(r"text-align\s*:\s*center", html, flags=re.IGNORECASE))
    background_image_count = len(re.findall(r"background-image\s*:", html, flags=re.IGNORECASE))
    border_radius_count = len(re.findall(r"border-radius\s*:", html, flags=re.IGNORECASE))
    row_widths = re.findall(r"width\s*:\s*(\d{1,3})%", html, flags=re.IGNORECASE)
    row_width_values = [int(value) for value in row_widths if value.isdigit()]
    small_image_count = 0
    for image in images:
        src = image.get("src", "")
        if any(token in src.lower() for token in ("icon-", "logo-", "avatar")):
            small_image_count += 1
    split_candidates = sum(1 for value in row_width_values if 25 <= value <= 75)
    is_centered = bool(text_align_center_count >= 2 or (
        headings
        and len(images) <= 1
        and len(links) <= 2
        and sum(len(value.split()) for value in headings[:1] + list(paragraphs[:1])) < 45
        and "text-align:center" in html.replace(" ", "").lower()
    ))
    has_split = split_candidates >= 2 and len(images) >= 1
    has_grid = len(images) >= 3 or len(headings) >= 3 or border_radius_count >= 3
    has_table = bool(table_headers and table_rows)
    button_like_count = len(
        re.findall(
            r"<a\b[^>]*(?:padding\s*:\s*\d|border-radius\s*:\s*\d|display\s*:\s*inline-block|class=\"[^\"]*\bbutton\b)",
            html,
            flags=re.IGNORECASE,
        )
    )
    layout = "list"
    if has_table:
        layout = "table"
    elif has_split:
        layout = "split"
    elif has_grid:
        layout = "grid"
    elif is_centered:
        layout = "centered"
    return {
        "layout": layout,
        "is_centered": is_centered,
        "has_split_columns": has_split,
        "has_grid": has_grid,
        "has_table": has_table,
        "button_count": max(button_like_count, len(links)),
        "background_image_count": background_image_count,
        "card_count": max(border_radius_count // 2, len(headings[1:]), len(images)),
        "small_image_count": min(small_image_count, len(images)),
        "table_columns": len(table_headers),
        "table_rows": len(table_rows),
    }


class CuratedAssetLocalizer:
    _download_cache: dict[str, bytes] = {}

    def __init__(self, output_root: Path, cache_root: Path | None = None) -> None:
        self.output_root = output_root
        self.cache_root = cache_root or output_root
        self.asset_dir = self.output_root / "assets" / "curated-images"
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir = self.output_root / "generated"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.map_path = self.generated_dir / "curated-asset-map.json"
        self.asset_map: dict[str, str] = {}
        if self.map_path.exists():
            loaded = json.loads(self.map_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.asset_map.update({str(key): str(value) for key, value in loaded.items()})
        self.cache_map: dict[str, str] = {}
        cache_map_path = self.cache_root / "generated" / "curated-asset-map.json"
        if cache_map_path.exists():
            loaded = json.loads(cache_map_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.cache_map.update({str(key): str(value) for key, value in loaded.items()})

    def _relative_for_examples(self, docs_relative_path: str) -> str:
        return f"../curated-images/{Path(docs_relative_path).name}"

    def _target_relative_path(self, filename: str) -> str:
        return f"assets/curated-images/{filename}"

    def _download(self, url: str) -> bytes | None:
        if url in self._download_cache:
            return self._download_cache[url]
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; pyzahidal-docs/1.0)"})
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310
                body = response.read()
        except Exception:
            return None
        self._download_cache[url] = body
        return body

    def _write_fallback(self, path: Path, url: str) -> None:
        if path.suffix.lower() == ".svg":
            label = _normalize_whitespace(Path(url).name) or "asset"
            svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'>"
                "<rect width='120' height='80' fill='#e2e8f0'/>"
                f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='#334155' font-size='10'>{escape(label)}</text>"
                "</svg>"
            )
            path.write_text(svg, encoding="utf-8")
            return
        path.write_bytes(CURATED_ONE_PIXEL_PNG)

    def localize(self, url: str) -> str:
        if not re.match(r"^https://assets\.[^/]+/", url):
            return url
        mapped = self.asset_map.get(url)
        if mapped:
            mapped_path = self.output_root / mapped
            if mapped_path.exists():
                return self._relative_for_examples(mapped)
        cache_mapped = self.cache_map.get(url)
        if cache_mapped:
            cache_path = self.cache_root / cache_mapped
            target_path = self.output_root / cache_mapped
            if cache_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if not target_path.exists():
                    shutil.copy2(cache_path, target_path)
                self.asset_map[url] = cache_mapped
                return self._relative_for_examples(cache_mapped)
        extension = Path(url).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}:
            extension = ".bin"
        filename = f"{sha1(url.encode('utf-8')).hexdigest()[:12]}{extension}"
        relative_path = self._target_relative_path(filename)
        target_path = self.output_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists():
            body = self._download(url)
            if body:
                target_path.write_bytes(body)
            else:
                self._write_fallback(target_path, url)
        self.asset_map[url] = relative_path
        return self._relative_for_examples(relative_path)

    def persist(self) -> None:
        self.map_path.write_text(json.dumps(self.asset_map, indent=2, sort_keys=True), encoding="utf-8")


def _pick(values: Sequence[object], index: int, default: object = "") -> object:
    if index < len(values):
        return values[index]
    return default


def _extract_source_data(html: str, localizer: CuratedAssetLocalizer | None) -> dict[str, object]:
    headings = []
    for level in ("h1", "h2", "h3", "h4"):
        headings.extend(_extract_tag_texts(html, level))
    paragraphs = _extract_tag_texts(html, "p")
    links = _extract_links(html)
    images = _extract_images(html)
    localized_images = [{"src": localizer.localize(image["src"]) if localizer else image["src"], "alt": image.get("alt", "")} for image in images]
    all_text = _normalize_whitespace(" ".join([*headings, *paragraphs, *[link["label"] for link in links]]))
    prices = re.findall(r"\$\s?\d+(?:[.,]\d+)?", all_text)
    percents = re.findall(r"\d+(?:\.\d+)?%", all_text)
    versions = CURATED_VERSION_RE.findall(all_text)
    dates = CURATED_DATE_RE.findall(all_text)
    headers, rows = _extract_table_data(html)
    groups = _curated_group_texts(headings, paragraphs)
    layout_flags = _curated_layout_flags(html, headings, paragraphs, localized_images, links, headers, rows)
    return {
        "headings": headings,
        "paragraphs": paragraphs,
        "links": links,
        "images": localized_images,
        "all_text": all_text,
        "prices": prices,
        "percents": percents,
        "versions": versions,
        "dates": dates,
        "table_headers": headers,
        "table_rows": rows,
        "groups": groups,
        "layout": layout_flags["layout"],
        "layout_flags": layout_flags,
        "source_html": html,
    }


def _is_usable_marker(value: str) -> bool:
    text = _normalize_whitespace(value)
    if len(text) < 3:
        return False
    lowered = text.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return False
    return True


def _curated_expected_markers(category: str, source: dict[str, object]) -> list[str]:
    headings = [str(value) for value in source.get("headings", []) if _is_usable_marker(str(value))]
    paragraphs = [str(value) for value in source.get("paragraphs", []) if _is_usable_marker(str(value))]
    links = [str(item.get("label", "")) for item in source.get("links", []) if isinstance(item, dict) and _is_usable_marker(str(item.get("label", "")))]
    image_alts = [str(item.get("alt", "")) for item in source.get("images", []) if isinstance(item, dict) and _is_usable_marker(str(item.get("alt", "")))]
    versions = [str(value) for value in source.get("versions", []) if _is_usable_marker(str(value))]
    dates = [str(value) for value in source.get("dates", []) if _is_usable_marker(str(value))]
    prices = [str(value) for value in source.get("prices", []) if _is_usable_marker(str(value))]
    percents = [str(value) for value in source.get("percents", []) if _is_usable_marker(str(value))]

    markers: list[str] = []
    if category == "Timelines":
        markers.extend(versions[:1])
        markers.extend(dates[:1])
        if len(paragraphs) >= 2:
            markers.append(paragraphs[1])
        markers.extend(headings[:1])
        detail = next((paragraph for paragraph in paragraphs if len(paragraph) >= 24), "")
        if detail:
            markers.append(detail)
    elif category == "Social":
        markers.extend(headings[:1])
        markers.extend(paragraphs[:1])
        markers.extend(image_alts[:3])
    elif category == "Avatars":
        if headings:
            markers.extend(headings[:1])
        markers.extend(paragraphs[:2])
    elif category == "Category Previews":
        markers.extend(headings[:3])
        markers.extend(prices[:2])
        markers.extend(links[:1])
    elif category == "FAQs":
        if len(headings) > 1:
            markers.extend(headings[1:3])
        else:
            markers.extend(headings[:1])
        markers.extend(paragraphs[:1])
        markers.extend(links[:1])
    elif category == "Pricing":
        markers.extend(headings[:1])
        markers.extend(prices[:2])
        markers.extend(links[:1])
    elif category == "Shopping Cart":
        markers.extend(headings[:1])
        markers.extend(prices[:2])
        markers.extend(links[:1])
    elif category == "Product Detail":
        markers.extend(headings[:2])
        markers.extend(prices[:1])
        detail = next((paragraph for paragraph in paragraphs if 12 <= len(paragraph) <= 110), "")
        if detail:
            markers.append(detail)
    elif category == "Order Summary":
        markers.extend(headings[:1])
        markers.extend(prices[:2])
        markers.extend(percents[:1])
    elif category == "Data Tables":
        markers.extend(headings[:1])
        markers.extend(links[:1])
        markers.extend(image_alts[:2])
    elif category == "Progress Bars":
        markers.extend(headings[:1])
        markers.extend(percents[:1])
    else:
        markers.extend(headings[:2])
        first_body = next((paragraph for paragraph in paragraphs if len(paragraph) >= 8), "")
        if first_body:
            markers.append(first_body)
        if links:
            markers.append(links[0])

    unique: list[str] = []
    seen_lower: set[str] = set()
    for marker in markers:
        normalized = _normalize_whitespace(marker)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen_lower:
            continue
        seen_lower.add(lowered)
        unique.append(normalized)
    return unique


def _build_curated_component(category: str, title: str, theme: str, source: dict[str, object]) -> object:
    headings = [str(value) for value in source.get("headings", [])]
    paragraphs = [str(value) for value in source.get("paragraphs", [])]
    links = [value for value in source.get("links", []) if isinstance(value, dict)]
    images = [value for value in source.get("images", []) if isinstance(value, dict)]
    prices = [str(value) for value in source.get("prices", [])]
    percents = [str(value) for value in source.get("percents", [])]
    versions = [str(value) for value in source.get("versions", [])]
    dates = [str(value) for value in source.get("dates", [])]
    table_headers = [str(value) for value in source.get("table_headers", [])]
    table_rows = [[str(cell) for cell in row] for row in source.get("table_rows", []) if isinstance(row, list)]
    groups = _source_groups(source)
    layout = _source_layout(source)
    layout_flags = _source_flags(source)

    heading_text = _pick(headings, 0, title)
    body_text = _pick(paragraphs, 0, f"Source-driven composition for {title}.")
    primary_link = links[0] if links else {"label": "Learn more", "href": "#"}
    secondary_link = links[1] if len(links) > 1 else None

    if category == "Headers":
        nav_items = [_menu_item_spec(str(link.get("label", "Link")), href=str(link.get("href", "#"))) for link in links[:6]]
        logo_src = str(images[0].get("src", "")) if images else None
        logo_alt = str(images[0].get("alt", "")) if images else ""
        if len(images) > 1 and "social" in title.lower():
            social_items = []
            for index, image in enumerate(images[1:5]):
                href = str(_pick(links, index, {"href": "#"})["href"]) if index < len(links) else "#"
                social_items.append(
                    _social_link_spec(
                        href=href,
                        icon_src=str(image.get("src", "")),
                        alt=str(image.get("alt", f"Social {index + 1}")),
                    )
                )
            return ui.Section(
                ui.Columns(
                    ui.Image(
                        logo_src or svg_data_url("Logo", 180, 55, "#e2e8f0", "#334155"),
                        alt=logo_alt or heading_text,
                        width="auto",
                        block=False,
                        styles={"max-width": "180px", "border-radius": "0"},
                        theme=theme,
                    ),
                    _curated_plain_icon_row(social_items, theme=theme, align="right", gap="24px"),
                    widths=["58%", "42%"],
                    gap="16px",
                    vertical_align="middle",
                ),
                theme=theme,
            )
        return ui.Header(
            heading_text,
            nav_items=nav_items,
            logo_src=logo_src or None,
            logo_alt=logo_alt,
            tagline=_pick(paragraphs, 0, None),
            meta_label=_pick(headings, 1, "Email kit"),
            theme=theme,
        )
    if category == "Footers":
        social_items = [_social_link_spec(label=str(link.get("label", "Link")), href=str(link.get("href", "#"))) for link in links[:5]]
        menu_items = [_menu_item_spec(str(link.get("label", "Link")), href=str(link.get("href", "#"))) for link in links[5:9]]
        legal_links = [_menu_item_spec(str(link.get("label", "Link")), href=str(link.get("href", "#"))) for link in links[9:13]]
        top_image_src = str(images[0].get("src", "")) if images else None
        return ui.Footer(
            heading_text,
            social_items=social_items,
            top_image_src=top_image_src or None,
            top_image_alt=str(images[0].get("alt", "")) if images else "",
            description=_pick(paragraphs, 0, body_text),
            menu_items=menu_items or None,
            legal_links=legal_links or None,
            disclaimer=_pick(paragraphs, 1, None),
            theme=theme,
        )
    if category == "Logos":
        logos = [_logo_spec(str(image.get("alt") or "Logo"), src=str(image.get("src", ""))) for image in images[:6]]
        return ui.Section(
            ui.Stack(
                ui.Heading(heading_text, level="small", align="center", theme=theme),
                ui.LogoStrip(logos if logos else [_logo_spec("Logo")], columns=min(5, len(logos)) if logos else None, theme=theme),
                ui.Text(body_text, size="small", tone="muted", align="center", theme=theme),
                gap="20px",
                align="center",
                theme=theme,
            ),
            padding="36px 24px",
            theme=theme,
        )
    if category == "HERO":
        actions = [ui.Button(str(primary_link.get("label", "Learn more")), href=str(primary_link.get("href", "#")), theme=theme)]
        if secondary_link:
            actions.append(ui.Button(str(secondary_link.get("label", "Details")), href=str(secondary_link.get("href", "#")), variant="secondary", theme=theme))
        meta_items = [_metric_spec(_pick(headings, index + 1, "Metric"), value) for index, value in enumerate((percents or prices)[:3])]
        if layout in {"centered", "grid"} and not layout_flags.get("has_split_columns"):
            hero_children: list[object] = [
                ui.Text(_pick(headings, 1, eyebrow := _pick(headings, 2, "Featured")), size="kicker", tone="accent", align="center", theme=theme),
                ui.Heading(heading_text, level="hero", align="center", theme=theme),
                ui.Text(body_text, align="center", tone="muted", theme=theme),
                ui.Inline(*actions, align="center", gap="12px", wrap=True, theme=theme),
            ]
            if images:
                hero_children.extend([ui.Spacer("18px"), _render_image_strip(images, theme, max_items=3, columns=min(3, len(images)))])
            if meta_items:
                hero_children.extend([ui.Spacer("18px"), ui.Stats(meta_items[:3], theme=theme)])
            return ui.Section(ui.Stack(*hero_children, gap="14px", align="center", theme=theme), theme=theme)
        media = None
        if images:
            media = ui.HeroMediaSpec(
                str(images[0].get("src", "")),
                alt=str(images[0].get("alt", heading_text)),
                title=_pick(headings, 1, "Preview"),
                body=_pick(paragraphs, 1, body_text),
            )
        return ui.Hero(
            eyebrow=_pick(headings, 2, None),
            title=heading_text,
            body=body_text,
            primary_action=_action_spec(str(primary_link.get("label", "Learn more")), href=str(primary_link.get("href", "#")), variant="primary"),
            secondary_action=(
                _action_spec(str(secondary_link.get("label", "Details")), href=str(secondary_link.get("href", "#")), variant="secondary")
                if secondary_link
                else None
            ),
            media=media,
            meta_items=meta_items or None,
            theme=theme,
        )
    if category == "Call to Action":
        actions = [_action_spec(str(primary_link.get("label", "Open")), href=str(primary_link.get("href", "#")), variant="primary")]
        if secondary_link:
            actions.append(_action_spec(str(secondary_link.get("label", "Learn more")), href=str(secondary_link.get("href", "#")), variant="ghost"))
        cta = ui.CallToAction(heading_text, body_text, actions, theme=theme)
        if images and layout == "grid":
            return ui.Section(
                ui.Stack(
                    cta,
                    _render_image_strip(images, theme, max_items=3, columns=min(3, len(images))),
                    gap="14px",
                    theme=theme,
                ),
                theme=theme,
            )
        if images:
            return ui.Surface(
                cta,
                background_image=str(images[0].get("src", "")),
                background_color="#1f2937",
                padding="24px",
                radius="16px",
                theme=theme,
            )
        return cta
    if category == "Coupons":
        return ui.Section(
            ui.Stack(
                ui.Heading(heading_text, level="small", theme=theme),
                ui.Text(body_text, theme=theme),
                ui.Button(str(primary_link.get("label", "Shop now")), href=str(primary_link.get("href", "#")), theme=theme),
                gap="10px",
                theme=theme,
            ),
            padding="24px",
            theme=theme,
        )
    if category == "Bento grids":
        if "even split image stats" in title.lower():
            feature_image = str(images[-1].get("src", "")) if images else svg_data_url("Analytics", 264, 220, "#dbeafe", "#1d4ed8")
            stats_heading = _pick(headings, 0, "API Calls")
            stats_value = _pick(paragraphs, 0, _pick(prices, 0, "25,000"))
            trend_text = _pick(table_headers, 1, "10% increase")
            report_label = str(primary_link.get("label", "View report"))
            report_href = str(primary_link.get("href", "#"))
            metric_specs = [
                {"label": _pick(paragraphs, 2, "Engine v2"), "value": _pick(paragraphs, 3, "75x"), "detail": _pick(paragraphs, 4, "faster"), "tone": "subtle"},
                {"label": _pick(paragraphs, 5, "Cost reduction"), "value": _pick(percents, 0, "50%"), "detail": _pick(paragraphs, 4, "faster"), "tone": "ghost"},
                {"label": _pick(paragraphs, 7, "Load time"), "value": _pick(paragraphs, 3, "75x"), "detail": _pick(paragraphs, 4, "faster"), "tone": "default"},
            ]
            top_row = ui.Columns(
                ui.Surface(
                    ui.Stack(
                        ui.Heading(stats_heading, level="small", theme=theme),
                        ui.Text(stats_value, theme=theme, styles={"font-size": "24px", "line-height": "32px", "font-weight": "700", "color": "#030712"}),
                        ui.Text(trend_text, size="small", tone="muted", theme=theme),
                        ui.Link(report_label, href=report_href, theme=theme, styles={"font-size": "12px", "font-weight": "500", "color": "#4f46e5"}),
                        gap="10px",
                        theme=theme,
                    ),
                    padding="16px",
                    tone="subtle",
                    radius="8px",
                    styles={"background": "#f9fafb", "border": "1px solid #d1d5db", "box-shadow": "none"},
                    theme=theme,
                ),
                ui.Image(feature_image, alt="", theme=theme, styles={"border-radius": "8px"}),
                widths=["50%", "50%"],
                gap="24px",
                vertical_align="middle",
            )
            stat_tiles = []
            for spec in metric_specs:
                stat_tiles.append(
                    ui.Surface(
                        ui.Stack(
                            ui.Text(spec["label"], size="small", theme=theme, styles={"font-weight": "600", "color": "#030712", "text-align": "center"}),
                            ui.Text(spec["value"], theme=theme, styles={"font-size": "48px", "line-height": "1.1", "font-weight": "500", "color": "#030712", "text-align": "center"}),
                            ui.Text(spec["detail"], size="small", tone="muted", theme=theme, align="center"),
                            gap="4px",
                            align="center",
                            theme=theme,
                        ),
                        padding="56px 0",
                        tone="ghost" if spec["tone"] == "ghost" else "subtle",
                        radius="8px",
                        styles={"background": "#f9fafb" if spec["tone"] == "subtle" else ("#f3f4f6" if spec["tone"] == "ghost" else "#ffffff"), "border": "0", "box-shadow": "none"},
                        theme=theme,
                    )
                )
            return ui.Section(
                ui.Stack(
                    top_row,
                    ui.Columns(*stat_tiles, widths=["33%", "33%", "33%"], gap="24px", vertical_align="middle"),
                    gap="24px",
                    theme=theme,
                ),
                theme=theme,
            )
        cards = []
        if groups:
            for group in groups[:4]:
                cards.append(_group_to_card(group, theme, compact=True))
        else:
            for index in range(max(3, min(len(headings), 4))):
                cards.append(
                    _group_to_card(
                        {"heading": _pick(headings, index, f"Card {index + 1}"), "paragraphs": [_pick(paragraphs, index, body_text)]},
                        theme,
                        compact=True,
                    )
                )
        children: list[object] = [ui.Columns(*cards[:3], widths=["34%", "33%", "33%"][: len(cards[:3])], gap="12px") if len(cards) >= 3 else ui.Stack(*cards, gap="12px", theme=theme)]
        if images:
            children.append(_render_image_strip(images, theme, max_items=4, columns=min(2, len(images))))
        if percents:
            children.append(ui.Stats([_metric_spec(_pick(headings, index + 3, f"Metric {index + 1}"), value, _pick(paragraphs, index + 2, None)) for index, value in enumerate(percents[:3])], theme=theme))
        if links:
            children.append(ui.Inline(*[ui.Button(str(link.get("label", "View")), href=str(link.get("href", "#")), variant="primary" if index == 0 else "secondary", theme=theme) for index, link in enumerate(links[:2])], gap="10px", theme=theme))
        return ui.Section(ui.Stack(*children, gap="14px", theme=theme), theme=theme)
    if category == "Feature":
        left = ui.Surface(
            ui.Stack(
                ui.Heading(heading_text, level="small", theme=theme),
                ui.Text(body_text, theme=theme),
                ui.Button(str(primary_link.get("label", "Discover")), href=str(primary_link.get("href", "#")), variant="ghost", theme=theme),
                gap="10px",
                theme=theme,
            ),
            padding="20px",
            theme=theme,
        )
        right = (
            _render_image_strip(images, theme, max_items=2, columns=min(2, len(images))) if len(images) > 1 else ui.Surface("", background_image=str(images[0].get("src", "")), background_color="#dbeafe", padding="180px 0", theme=theme)
        ) if images else ui.Surface(ui.Text(_pick(paragraphs, 1, body_text), theme=theme), padding="20px", theme=theme)
        return ui.Columns(left, right, widths=["48%", "52%"], gap="16px")
    if category == "Images":
        if len(images) > 1:
            return _render_image_strip(images, theme, max_items=min(4, len(images)), columns=2 if layout in {"grid", "split"} else min(3, len(images)))
        src = str(images[0].get("src", "")) if images else svg_data_url("Image", 640, 320, "#e2e8f0", "#334155")
        alt = str(images[0].get("alt", heading_text)) if images else heading_text
        return ui.Image(src, alt=alt, theme=theme)
    if category == "Stats":
        values = percents[:]
        values.extend(prices[:])
        if not values:
            values = ["42%", "18%", "$12k"]
        items = []
        for index, value in enumerate(values[:3]):
            items.append(_metric_spec(_pick(headings, index, f"Metric {index + 1}"), value, _pick(paragraphs, index, None)))
        stats = ui.Stats(items, theme=theme)
        if images:
            return ui.Surface(stats, background_image=str(images[0].get("src", "")), background_color="#1f2937", padding="22px", radius="18px", theme=theme)
        return stats
    if category == "Social":
        if images:
            social_items = []
            for index, image in enumerate(images[:5]):
                href = str(_pick(links, index, {"href": "#"})["href"]) if index < len(links) else "#"
                social_items.append(
                    _social_link_spec(
                        href=href,
                        icon_src=str(image.get("src", "")),
                        alt=str(image.get("alt", _pick(links, index, {"label": "social"}).get("label", "social"))),
                    )
                )
            if "stacked" in title.lower() and "label" in title.lower():
                return ui.Section(
                    ui.Stack(
                        ui.Heading(_pick(headings, 0, "Connect with us"), level="small", align="center", theme=theme),
                        _curated_stacked_social_row(social_items, theme=theme),
                        ui.Text(_pick(paragraphs, 0, body_text), size="small", tone="muted", align="center", theme=theme),
                        gap="12px",
                        align="center",
                        theme=theme,
                    ),
                    theme=theme,
                )
            nodes: list[object] = [
                ui.Heading(_pick(headings, 0, "Connect with us"), level="small", align="center", theme=theme),
                ui.Text(_pick(paragraphs, 0, body_text), size="small", tone="muted", align="center", theme=theme),
                ui.SocialLinks(social_items, mode="icon", theme=theme),
            ]
            if links:
                nodes.append(
                    ui.Inline(
                        *[
                            ui.Button(
                                str(link.get("label", "Open")),
                                href=str(link.get("href", "#")),
                                variant="secondary" if index else "primary",
                                theme=theme,
                            )
                            for index, link in enumerate(links[:2])
                        ],
                        align="center",
                        gap="10px",
                        theme=theme,
                    )
                )
            return ui.Section(ui.Stack(*nodes, gap="14px", align="center", theme=theme), theme=theme)
        return ui.SocialLinks([_social_link_spec(label=str(link.get("label", "Link")), href=str(link.get("href", "#"))) for link in links[:6]], theme=theme)
    if category == "Blog":
        cards = []
        card_total = max(2, min(3, len(groups) or len(headings) or len(images) or 2))
        for index in range(card_total):
            cards.append(
                ui.Surface(
                    ui.Stack(
                        ui.Image(str(_pick(images, index, {"src": svg_data_url(f'Post {index + 1}', 320, 200, '#dbeafe', '#1d4ed8')})["src"]), alt=str(_pick(images, index, {"alt": f"Post {index + 1}"})["alt"]), theme=theme),
                        ui.Heading(_pick(headings, index, f"Post {index + 1}"), level="small", theme=theme),
                        ui.Text(_pick(paragraphs, index, body_text), size="small", theme=theme),
                        ui.Button(str(_pick(links, index, {"label": "Read more"}).get("label", "Read more")), href=str(_pick(links, index, {"href": "#"}).get("href", "#")), variant="ghost", theme=theme),
                        gap="10px",
                        theme=theme,
                    ),
                    padding="16px",
                    theme=theme,
                )
            )
        return ui.Columns(*cards[:3], gap="14px", widths=["34%", "33%", "33%"][: len(cards[:3])]) if len(cards) >= 3 else ui.Columns(*cards, gap="14px")
    if category == "Content":
        return ui.Section(
            ui.Stack(
                ui.Text(_pick(headings, 1, "Content"), size="kicker", theme=theme),
                ui.Heading(heading_text, level="section", theme=theme),
                ui.Text(body_text, theme=theme),
                ui.Text(_pick(paragraphs, 1, ""), size="small", tone="muted", theme=theme),
                gap="10px",
                theme=theme,
            ),
            theme=theme,
        )
    if category == "FAQs":
        qa = []
        question_candidates = headings[1:] if len(headings) > 1 else [heading_text]
        for index, question in enumerate(question_candidates[:4]):
            qa.append(_faq_spec(question, _pick(paragraphs, index, body_text)))
        return ui.FAQ(qa, theme=theme)
    if category == "Team":
        members = []
        for index, image in enumerate(images[:4]):
            members.append(
                ui.TeamMemberSpec(
                    name=_pick(headings, index, f"Member {index + 1}"),
                    role=_pick(paragraphs, index, "Team"),
                    image=str(image.get("src", "")),
                    meta=_pick(paragraphs, index + 1, ""),
                )
            )
        if not members:
            members = [ui.TeamMemberSpec(name=heading_text, role=body_text, image=svg_data_url("Team", 96, 96, "#dbeafe", "#1d4ed8"))]
        if len(members) >= 3:
            columns = []
            social_chunks = [links[index * 3 : index * 3 + 3] for index in range(3)]
            social_images = images[len(members) :]
            for index, member in enumerate(members[:3]):
                member_links = [
                    _social_link_spec(href=str(link.get("href", "#")), icon_src=str(social_images[index * 3 + offset].get("src", "")), alt=str(link.get("label", "social")))
                    for offset, link in enumerate(social_chunks[index])
                    if len(social_images) > index * 3 + offset
                ]
                columns.append(_curated_team_member_card(member, member_links, theme=theme))
            return ui.Columns(*columns, widths=["33%", "33%", "33%"], gap="16px")
        return ui.Team(members, theme=theme)
    if category == "Testimonials":
        items = []
        for index, group in enumerate(groups[:3] or [{"heading": _pick(headings, 1, "Customer"), "paragraphs": [_pick(paragraphs, 0, body_text)]}]):
            quote = _pick(group.get("paragraphs", []), 0, body_text)
            author = group.get("heading") or _pick(headings, index + 1, f"Customer {index + 1}")
            items.append(ui.TestimonialSpec(quote, author))
        testimonial = ui.Testimonials(items, theme=theme)
        if links:
            return ui.Stack(testimonial, ui.Button(str(primary_link.get("label", "Read more")), href=str(primary_link.get("href", "#")), theme=theme), align="center", gap="12px", theme=theme)
        return testimonial
    if category == "Timelines":
        date_candidates = [value for value in dates if value]
        if not date_candidates:
            date_candidates = [value for value in paragraphs if CURATED_DATE_RE.search(value)]
        category_candidates = [value for value in paragraphs if value and value not in date_candidates and len(value.split()) <= 3]
        detail_candidates = [value for value in paragraphs if value and value not in date_candidates and value not in category_candidates]
        for price in prices:
            if price and price not in detail_candidates:
                detail_candidates.append(price)
        title_candidates = headings[:] if headings else ["Changelog update"]
        count = max(1, min(len(title_candidates), 4))
        steps = []
        for index in range(count):
            steps.append(
                _timeline_step_spec(
                    _pick(versions, index, _pick(versions, 0, f"v{index + 1}.0.0")),
                    _pick(date_candidates, index, _pick(date_candidates, 0, f"{index + 1} Jan")),
                    _pick(category_candidates, index, _pick(category_candidates, 0, "Update")),
                    _pick(title_candidates, index, f"Update {index + 1}"),
                    _pick(detail_candidates, index, _pick(detail_candidates, 0, body_text)),
                )
            )
        return ui.Timeline(steps, theme=theme)
    if category == "Pricing":
        plans = []
        price_values = prices or ["$29"]
        for index, price in enumerate(price_values[:2]):
            plan_name = _pick(headings, index, f"Plan {index + 1}")
            plans.append(
                ui.PricingPlanSpec(
                    plan_name,
                    price,
                    _pick(paragraphs, index, body_text),
                    badge=_pick(headings, index + 2, "") if index == 1 else "",
                    featured=index == 1 or len(price_values) == 1,
                    features=[_pick(paragraphs, index + 1, "Includes core features"), _pick(paragraphs, index + 2, "Email support")],
                    action=_action_spec(str(_pick(links, index, {"label": "Choose plan"}).get("label", "Choose plan")), href=str(_pick(links, index, {"href": "#"}).get("href", "#")), variant="primary" if index == 1 else "secondary"),
                )
            )
        if len(price_values) >= 3:
            extra_price = price_values[2]
            plans.append(
                ui.PricingPlanSpec(
                    _pick(headings, 2, "Enterprise"),
                    extra_price,
                    _pick(paragraphs, 2, body_text),
                    featured=False,
                    features=[_pick(paragraphs, 3, "Custom onboarding"), _pick(paragraphs, 4, "Priority support")],
                    action=_action_spec(str(_pick(links, 2, {"label": "Contact sales"}).get("label", "Contact sales")), href=str(_pick(links, 2, {"href": "#"}).get("href", "#")), variant="secondary"),
                )
            )
        if layout == "split":
            cards = []
            for plan in plans[:3]:
                card_items = [
                    ui.Text(plan.badge, size="kicker", tone="accent", theme=theme) if plan.badge else "",
                    ui.Heading(plan.name, level="small", theme=theme),
                    ui.Text(plan.price, theme=theme),
                    ui.Text(plan.description, size="small", tone="muted", theme=theme),
                    ui.Button(plan.action.label, href=plan.action.href, variant=plan.action.variant, theme=theme),
                ]
                cards.append(ui.Surface(ui.Stack(*[item for item in card_items if item], gap="8px", theme=theme), padding="18px", tone="featured" if plan.featured else "default", theme=theme))
            return ui.Columns(*cards, widths=["50%", "50%"] if len(cards) == 2 else ["34%", "33%", "33%"], gap="14px")
        return ui.Pricing(plans[:3], theme=theme)
    if category == "Product Lists":
        products = []
        for index in range(max(2, min(len(headings), 3))):
            image_src = str(_pick(images, index, {"src": ""}).get("src", ""))
            products.append(
                ui.ProductSpec(
                    _pick(headings, index, f"Product {index + 1}"),
                    _pick(prices, index, "$0"),
                    _pick(paragraphs, index, body_text),
                    image_src=image_src,
                    rating=_pick(percents, index, ""),
                    reviews=_pick(paragraphs, index + 1, ""),
                    action=_action_spec(str(_pick(links, index, {"label": "View product"}).get("label", "View product")), href=str(_pick(links, index, {"href": "#"}).get("href", "#")), variant="secondary"),
                )
            )
        return ui.ProductList(products[:4], theme=theme)
    if category == "Product Detail":
        detail_text = _first_descriptive_paragraph(paragraphs, *prices) or body_text
        if len(images) > 1:
            return ui.Columns(
                ui.Stack(
                    ui.Heading(heading_text, level="section", theme=theme),
                    ui.Text(_pick(prices, 0, "$0"), theme=theme),
                    ui.Text(detail_text, theme=theme),
                    ui.Button(str(primary_link.get("label", "View product")), href=str(primary_link.get("href", "#")), theme=theme),
                    gap="10px",
                    theme=theme,
                ),
                _render_image_strip(images, theme, max_items=min(4, len(images)), columns=2),
                widths=["42%", "58%"],
                gap="16px",
            )
        return ui.ProductDetail(heading_text, _pick(prices, 0, "$0"), detail_text, str(_pick(images, 0, {"src": ""}).get("src", "")), theme=theme)
    if category == "Category Previews":
        intro_heading = _pick(headings, 0, heading_text)
        intro_body = _pick(paragraphs, 0, body_text)
        card_titles = headings[1:] if len(headings) > 1 else [intro_heading]
        price_candidates = [value for value in paragraphs if "$" in value]
        cards: list[object] = []
        card_count = max(1, min(3, len(card_titles) or len(images) or 1))
        for index in range(card_count):
            image = _pick(images, index, {"src": svg_data_url(f"Category {index + 1}", 320, 220, "#e2e8f0", "#334155"), "alt": _pick(card_titles, index, "Category")})
            price = _pick(price_candidates, index, _pick(prices, index, ""))
            action_label = str(_pick(links, 0, {"label": "Shop now"}).get("label", "Shop now"))
            action_href = str(_pick(links, 0, {"href": "#"}).get("href", "#"))
            card_items: list[object] = [
                ui.Image(str(image.get("src", "")), alt=str(image.get("alt", _pick(card_titles, index, "Category"))), theme=theme),
                ui.Heading(_pick(card_titles, index, f"Category {index + 1}"), level="small", theme=theme),
            ]
            if price:
                card_items.append(ui.Text(price, size="small", tone="muted", theme=theme))
            card_items.append(ui.Button(action_label, href=action_href, variant="secondary", theme=theme))
            cards.append(ui.Surface(ui.Stack(*card_items, gap="10px", theme=theme), padding="16px", theme=theme))
        widths = ["34%", "33%", "33%"] if len(cards) == 3 else (["50%", "50%"] if len(cards) == 2 else None)
        return ui.Section(ui.Stack(ui.Heading(intro_heading, level="section", theme=theme), ui.Text(intro_body, theme=theme), ui.Columns(*cards, widths=widths, gap="14px"), gap="14px", theme=theme), theme=theme)
    if category == "Shopping Cart":
        cart_rows = []
        if table_rows:
            for row in table_rows[:4]:
                if len(row) >= 3:
                    cart_rows.append(ui.CartItemSpec(row[0], str(row[1]), row[2]))
        if not cart_rows:
            cart_rows = [ui.CartItemSpec(_pick(headings, 0, "Item"), "1", _pick(prices, 0, "$0"))]
        if first_link_label := str(primary_link.get("label", "")).strip():
            headers = ["Item", "Qty", "Price", "Action"]
            rows = [[row.name, row.qty, row.price, first_link_label] for row in cart_rows]
            return ui.DataTable(headers=headers, rows=rows, compact=True, striped=True, theme=theme)
        return ui.ShoppingCart(cart_rows, theme=theme)
    if category == "Reviews":
        review_items = []
        for index in range(max(2, min(len(paragraphs), 3))):
            review_items.append(
                ui.ReviewSpec(
                    quote=_pick(paragraphs, index, body_text),
                    author=_pick(headings, index + 1, f"Reviewer {index + 1}"),
                    src=str(_pick(images, index, {"src": ""}).get("src", "")),
                    rating="★★★★★" if index == 0 else "★★★★☆",
                )
            )
        review_component = ui.Reviews(review_items, theme=theme)
        if layout == "split" and links:
            return ui.Columns(review_component, ui.Surface(ui.Stack(ui.Heading(_pick(headings, 0, "Customer story"), level="small", theme=theme), ui.Text(body_text, theme=theme), ui.Button(str(primary_link.get("label", "Read more")), href=str(primary_link.get("href", "#")), theme=theme), gap="10px", theme=theme), padding="20px", theme=theme), widths=["60%", "40%"], gap="14px")
        return review_component
    if category == "Order Summary":
        summary_rows = []
        if table_rows:
            for row in table_rows[:6]:
                if len(row) >= 2:
                    summary_rows.append((row[0], row[-1]))
        if not summary_rows:
            summary_rows = [("Subtotal", _pick(prices, 0, "$0")), ("Total", _pick(prices, 1, _pick(prices, 0, "$0")))]
        progress = None
        if percents:
            try:
                progress = int(float(percents[0].replace("%", "")))
            except ValueError:
                progress = None
        summary = ui.OrderSummary(summary_rows, progress=progress, theme=theme)
        if images:
            return ui.Stack(summary, _render_image_strip(images, theme, max_items=2, columns=min(2, len(images))), gap="14px", theme=theme)
        return summary
    if category == "Containers":
        return ui.Container(
            ui.Stack(
                ui.Text(heading_text, size="kicker", theme=theme),
                ui.Text(body_text, theme=theme),
                ui.Text(_pick(paragraphs, 1, ""), size="small", tone="muted", theme=theme),
                gap="8px",
                theme=theme,
            ),
            theme=theme,
        )
    if category == "Grids":
        column_count = 4 if "4 columns" in title.lower() else 3
        widths = ["25%"] * 4 if column_count == 4 else ["34%", "33%", "33%"]
        cards = []
        for index in range(column_count):
            cards.append(
                ui.Surface(
                    ui.Stack(
                        ui.Heading(_pick(headings, index, f"Column {index + 1}"), level="small", theme=theme),
                        ui.Text(_pick(paragraphs, index, f"Column {index + 1}"), theme=theme),
                        gap="8px",
                        theme=theme,
                    ),
                    padding="16px",
                    theme=theme,
                )
            )
        return ui.Stack(
            ui.Heading(heading_text, level="small", theme=theme),
            ui.Columns(*cards, widths=widths, gap="12px"),
            gap="10px",
            theme=theme,
        )
    if category == "Spacing":
        spacer_size = "32px"
        for candidate in re.findall(r"\d+px", " ".join(paragraphs)):
            spacer_size = candidate
            break
        if "divider" in title.lower() and images:
            social_items = [_social_link_spec(href="#", icon_src=str(image.get("src", "")), alt=str(image.get("alt", "social"))) for image in images[:5]]
            return ui.Columns(
                ui.Divider(theme=theme),
                _curated_plain_icon_row(social_items[:4], theme=theme, gap="16px"),
                ui.Divider(theme=theme),
                widths=["39%", "22%", "39%"],
                gap="12px",
                vertical_align="middle",
            )
        return ui.Stack(
            ui.Text(_pick(paragraphs, 0, heading_text), theme=theme),
            ui.Spacer(spacer_size),
            ui.Text(_pick(paragraphs, 1, body_text), theme=theme),
            gap="0",
            theme=theme,
        )
    if category == "Buttons":
        button_nodes = []
        for index, link in enumerate(links[:5]):
            button_nodes.append(
                ui.Button(
                    str(link.get("label", f"Action {index + 1}")),
                    href=str(link.get("href", "#")),
                    icon_src=str(images[index].get("src", "")) if index < len(images) else None,
                    icon_alt=str(images[index].get("alt", "")) if index < len(images) else "",
                    variant="primary" if index == 0 else "secondary",
                    theme=theme,
                )
            )
        return ui.Inline(*button_nodes, gap="10px", theme=theme) if button_nodes else ui.Button("Action", href="#", theme=theme)
    if category == "Pills":
        labels = headings[:]
        labels.extend([paragraph.split(" ")[0] for paragraph in paragraphs if paragraph])
        if not labels:
            labels = ["Healthy", "Warning", "Critical"]
        tones = ["success", "warning", "danger", "default"]
        pills = [ui.Pill(label, tone=tones[index % len(tones)], theme=theme) for index, label in enumerate(labels[:4])]
        return ui.Inline(*pills, gap="8px", theme=theme)
    if category == "Avatars":
        if len(images) > 1:
            return ui.Stack(
                ui.AvatarGroup(
                    [_avatar_spec(str(image.get("src", "")), alt=str(image.get("alt", f'Avatar {index + 1}'))) for index, image in enumerate(images[:5])],
                    size="52px",
                    overlap="16px",
                    theme=theme,
                ),
                ui.Text(body_text, size="small", tone="muted", align="center", theme=theme),
                gap="12px",
                align="center",
                theme=theme,
            )
        image_src = str(_pick(images, 0, {"src": svg_data_url("A", 56, 56, "#dbeafe", "#1d4ed8")}).get("src", ""))
        name = _pick(headings, 0, _pick(paragraphs, 0, "Person"))
        detail = _pick(paragraphs, 1, _pick(paragraphs, 0, "Role"))
        return ui.Inline(
            ui.Avatar(image_src, alt=str(_pick(images, 0, {"alt": name}).get("alt", name)), size="56px"),
            ui.Stack(ui.Text(name, theme=theme), ui.Text(detail, size="small", tone="muted", theme=theme), gap="6px", theme=theme),
            gap="12px",
            theme=theme,
        )
    if category == "Progress Bars":
        value = 50
        if percents:
            try:
                value = int(float(percents[0].replace("%", "")))
            except ValueError:
                value = 50
        return ui.Stack(
            ui.Text(heading_text, theme=theme),
            ui.ProgressBar(value, theme=theme),
            ui.Text(f"{value}% complete", size="small", tone="muted", theme=theme),
            gap="8px",
            theme=theme,
        )
    if category == "Data Tables":
        headers = table_headers[:]
        rows = table_rows[:6]
        if not rows and images and links:
            headers = ["Integration", "Service", "Action"]
            synthesized_rows = []
            for index, link in enumerate(links[: min(len(links), 6)]):
                image = images[min(index + 1, len(images) - 1)] if len(images) > 1 else images[0]
                service_label = str(image.get("alt", "")) or str(link.get("label", f"Service {index + 1}"))
                action_label = str(link.get("label", "Manage"))
                synthesized_rows.append(
                    [
                        _pick(headings, index + 1, service_label),
                        ui.Inline(
                            ui.IconLink(
                                href=str(link.get("href", "#")),
                                icon_src=str(image.get("src", "")),
                                alt=service_label,
                                theme=theme,
                                size="32px",
                                shape="rounded",
                            ),
                            ui.Text(service_label, size="small", theme=theme),
                            gap="10px",
                            theme=theme,
                        ),
                        ui.Button(action_label, href=str(link.get("href", "#")), variant="ghost", theme=theme),
                    ]
                )
            rows = synthesized_rows
        elif not headers:
            headers = ["Name", "Status", "Action"]
            rows = [[_pick(headings, 0, "Record"), _pick(paragraphs, 0, "Active"), str(primary_link.get("label", "View"))]]
        first_link_label = str(primary_link.get("label", "")).strip()
        if first_link_label and rows and all(all(isinstance(cell, str) for cell in row) for row in rows) and not any(first_link_label in " ".join(str(cell) for cell in row) for row in rows):
            if len(headers) < 3:
                headers = [*headers, "Action"]
            rows.append([_pick(headings, 0, "Record"), _pick(paragraphs, 0, "Active"), first_link_label])
        normalized_rows: list[list[object]] = []
        for row_index, row in enumerate(rows):
            built_row: list[object] = []
            for col_index, cell in enumerate(row[: len(headers)]):
                header_name = headers[col_index].lower()
                cell_value: object = cell
                if "status" in header_name or "health" in header_name:
                    if hasattr(cell, "render") and callable(cell.render):
                        cell_value = cell
                    else:
                        tone = "success"
                        if any(word in str(cell).lower() for word in ("risk", "warning", "pending")):
                            tone = "warning"
                        if any(word in str(cell).lower() for word in ("at risk", "failed", "danger", "blocked")):
                            tone = "danger"
                        cell_value = ui.Pill(str(cell), tone=tone, theme=theme)
                elif "action" in header_name:
                    if hasattr(cell, "render") and callable(cell.render):
                        cell_value = cell
                    else:
                        href = str(_pick(links, row_index, {"href": "#"}).get("href", "#"))
                        cell_value = ui.Button(str(cell), href=href, variant="ghost", theme=theme)
                elif col_index == 1 and row_index < len(images) and layout_flags.get("small_image_count", 0):
                    cell_value = ui.Inline(
                        ui.IconLink(
                            href=str(_pick(links, row_index, {"href": "#"}).get("href", "#")),
                            icon_src=str(images[row_index].get("src", "")),
                            alt=str(images[row_index].get("alt", cell)),
                            theme=theme,
                            size="32px",
                            shape="rounded",
                        ),
                        ui.Text(str(cell), size="small", theme=theme),
                        gap="10px",
                        theme=theme,
                    )
                built_row.append(cell_value)
            normalized_rows.append(built_row)
        return ui.DataTable(headers=headers, rows=normalized_rows, compact=True, striped=True, theme=theme)
    return ui.Section(
        ui.Stack(
            ui.Heading(heading_text, level="small", theme=theme),
            ui.Text(body_text, theme=theme),
            ui.Button(str(primary_link.get("label", "Learn more")), href=str(primary_link.get("href", "#")), theme=theme),
            gap="10px",
            theme=theme,
        ),
        theme=theme,
    )


def _curated_complexity_score(source: dict[str, object]) -> float:
    headings = [str(value) for value in source.get("headings", []) if str(value).strip()]
    paragraphs = [str(value) for value in source.get("paragraphs", []) if str(value).strip()]
    links = [value for value in source.get("links", []) if isinstance(value, dict)]
    images = [value for value in source.get("images", []) if isinstance(value, dict)]
    table_headers = [str(value) for value in source.get("table_headers", []) if str(value).strip()]
    table_rows = [value for value in source.get("table_rows", []) if isinstance(value, list)]
    text_word_count = len(re.findall(r"[A-Za-z0-9$%'-]+", str(source.get("all_text", ""))))
    return (
        len(images) * 3.0
        + len(links) * 2.0
        + len(table_headers) * 1.5
        + len(table_rows) * 2.0
        + len(headings) * 0.5
        + len(paragraphs) * 0.5
        + min(text_word_count, 500) / 100
    )


def _select_richest_curated_targets(source_sections: dict[tuple[str, str], dict[str, object]]) -> dict[str, dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for target in CURATED_TARGETS:
        candidates = [entry for (category, _), entry in source_sections.items() if category == target.category]
        if not candidates:
            continue
        richest: dict[str, object] | None = None
        richest_score = -1.0
        for entry in candidates:
            html = str(entry.get("section", {}).get("iframeHtml", ""))
            source_data = _extract_source_data(html, None)
            score = _curated_complexity_score(source_data)
            title = str(entry.get("title", ""))
            if score > richest_score or (score == richest_score and title < str(richest.get("title", "~"))):
                richest = entry
                richest_score = score
        if richest:
            selected[target.category] = richest
    return selected


def _curated_code_snippet(category: str, title: str, theme: str, source: dict[str, object]) -> str:
    headings = [str(value) for value in source.get("headings", []) if str(value).strip()]
    paragraphs = [str(value) for value in source.get("paragraphs", []) if str(value).strip()]
    links = [value for value in source.get("links", []) if isinstance(value, dict)]
    images = [value for value in source.get("images", []) if isinstance(value, dict)]
    prices = [str(value) for value in source.get("prices", []) if str(value).strip()]
    percents = [str(value) for value in source.get("percents", []) if str(value).strip()]
    table_headers = [str(value) for value in source.get("table_headers", []) if str(value).strip()]
    table_rows = [[str(cell) for cell in row] for row in source.get("table_rows", []) if isinstance(row, list)]
    layout = _source_layout(source)

    heading_text = _pick(headings, 0, title)
    body_text = _pick(paragraphs, 0, f"Source-driven composition for {title}.")
    primary_link = links[0] if links else {"label": "Learn more", "href": "#"}
    secondary_link = links[1] if len(links) > 1 else {"label": "Details", "href": "#"}
    first_image_src = str(images[0].get("src", "")) if images else svg_data_url("Preview", 640, 320, "#e2e8f0", "#334155")
    first_image_alt = str(images[0].get("alt", heading_text)) if images else str(heading_text)
    detail_text = _first_descriptive_paragraph(paragraphs, *prices) or body_text

    if category == "Product Lists":
        products: list[dict[str, str]] = []
        for index in range(max(2, min(4, len(headings)))):
            products.append(
                {
                    "name": str(_pick(headings, index, f"Product {index + 1}")),
                    "price": str(_pick(prices, index, "$0")),
                    "description": str(_pick(paragraphs, index, body_text)),
                    "image": str(_pick(images, index, {"src": first_image_src}).get("src", first_image_src)),
                    "rating": str(_pick(source.get("percents", []), index, "")),
                    "reviews": str(_pick(paragraphs, index + 1, "")),
                    "action": {"label": str(_pick(links, index, {"label": "View product"}).get("label", "View product")), "href": str(_pick(links, index, {"href": "#"}).get("href", "#")), "variant": "secondary"},
                }
            )
        return dedent(
            f"""
            from pyzahidal import ProductList

            component = ProductList(
                products={products!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Product Detail":
        if len(images) > 1:
            gallery_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[:4]]
            return dedent(
                f"""
                from pyzahidal import Button, Columns, Heading, ImageGroup, Stack, Text

                component = Columns(
                    Stack(
                        Heading({str(_pick(headings, 0, "Featured product"))!r}, level="section", theme={theme!r}),
                        Text({str(_pick(prices, 0, "$0"))!r}, theme={theme!r}),
                        Text({str(detail_text)!r}, theme={theme!r}),
                        Button({str(primary_link.get("label", "View product"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                        gap="10px",
                        theme={theme!r},
                    ),
                    ImageGroup(
                        items={gallery_items!r},
                        columns=2,
                        gap="10px",
                        theme={theme!r},
                    ),
                    widths=["42%", "58%"],
                    gap="16px",
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import ProductDetail

            component = ProductDetail(
                {str(_pick(headings, 0, "Featured product"))!r},
                {str(_pick(prices, 0, "$0"))!r},
                {str(detail_text)!r},
                image_src={first_image_src!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Shopping Cart":
        cart_rows = []
        for row in table_rows[:4]:
            if len(row) >= 3:
                cart_rows.append({"name": row[0], "qty": row[1], "price": row[2]})
        if not cart_rows:
            cart_rows = [{"name": str(heading_text), "qty": "1", "price": str(_pick(prices, 0, "$0"))}]
        first_link_label = str(primary_link.get("label", "")).strip()
        if first_link_label:
            rows = [[row["name"], row["qty"], row["price"], first_link_label] for row in cart_rows]
            return dedent(
                f"""
                from pyzahidal import DataTable

                component = DataTable(
                    headers={["Item", "Qty", "Price", "Action"]!r},
                    rows={rows!r},
                    compact=True,
                    striped=True,
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import ShoppingCart

            component = ShoppingCart(
                {cart_rows!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Data Tables":
        headers = table_headers[:]
        rows = table_rows[:6]
        if not rows and images and links:
            headers = ["Integration", "Service", "Action"]
            rich_rows = []
            for index, link in enumerate(links[: min(len(links), 6)]):
                image = images[min(index + 1, len(images) - 1)] if len(images) > 1 else images[0]
                service_label = str(image.get("alt", "")) or str(link.get("label", f"Service {index + 1}"))
                rich_rows.append(
                    [
                        str(_pick(headings, index + 1, service_label)),
                        {
                            "href": str(link.get("href", "#")),
                            "icon_src": str(image.get("src", first_image_src)),
                            "label": service_label,
                        },
                        {
                            "label": str(link.get("label", "Manage")),
                            "href": str(link.get("href", "#")),
                        },
                    ]
                )
            return dedent(
                f"""
                from pyzahidal import Button, DataTable, IconLink, Inline, Text

                component = DataTable(
                    headers={headers!r},
                    rows=[
                        [
                            row[0],
                            Inline(
                                IconLink(href=row[1]["href"], icon_src=row[1]["icon_src"], alt=row[1]["label"], theme={theme!r}, size="32px", shape="rounded"),
                                Text(row[1]["label"], size="small", theme={theme!r}),
                                gap="10px",
                                theme={theme!r},
                            ),
                            Button(row[2]["label"], href=row[2]["href"], variant="ghost", theme={theme!r}),
                        ]
                        for row in {rich_rows!r}
                    ],
                    compact=True,
                    striped=True,
                    theme={theme!r},
                    )
                    """
                ).strip()
        if not headers:
            headers = ["Name", "Status", "Action"]
            rows = [[str(heading_text), str(_pick(paragraphs, 0, "Active")), str(primary_link.get("label", "Open"))]]
        return dedent(
            f"""
            from pyzahidal import DataTable

            component = DataTable(
                headers={headers!r},
                rows={rows!r},
                compact=True,
                striped=True,
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Pricing":
        plans = [
            {
                "name": str(_pick(headings, 0, "Starter")),
                "price": str(_pick(prices, 0, "$9")),
                "description": str(_pick(paragraphs, 0, body_text)),
                "features": [str(_pick(paragraphs, 1, "Docs access")), str(_pick(paragraphs, 2, "Priority support"))],
                "action": {"label": str(primary_link.get("label", "Choose plan")), "href": str(primary_link.get("href", "#")), "variant": "primary"},
            },
            {
                "name": str(_pick(headings, 1, "Scale")),
                "price": str(_pick(prices, 1, "$29")),
                "description": str(_pick(paragraphs, 1, body_text)),
                "features": [str(_pick(paragraphs, 2, "Unlimited seats")), str(_pick(paragraphs, 3, "Shared workspace"))],
                "action": {"label": str(secondary_link.get("label", "Learn more")), "href": str(secondary_link.get("href", "#")), "variant": "secondary"},
            },
        ]
        if layout == "split":
            return dedent(
                f"""
                from pyzahidal import Button, Columns, Heading, Stack, Surface, Text

                component = Columns(
                    Surface(
                        Stack(
                            Heading({plans[0]["name"]!r}, level="small", theme={theme!r}),
                            Text({plans[0]["price"]!r}, theme={theme!r}),
                            Text({plans[0]["description"]!r}, size="small", tone="muted", theme={theme!r}),
                            Button({plans[0]["action"]["label"]!r}, href={plans[0]["action"]["href"]!r}, variant={plans[0]["action"]["variant"]!r}, theme={theme!r}),
                            gap="8px",
                            theme={theme!r},
                        ),
                        padding="18px",
                        theme={theme!r},
                    ),
                    Surface(
                        Stack(
                            Heading({plans[1]["name"]!r}, level="small", theme={theme!r}),
                            Text({plans[1]["price"]!r}, theme={theme!r}),
                            Text({plans[1]["description"]!r}, size="small", tone="muted", theme={theme!r}),
                            Button({plans[1]["action"]["label"]!r}, href={plans[1]["action"]["href"]!r}, variant={plans[1]["action"]["variant"]!r}, theme={theme!r}),
                            gap="8px",
                            theme={theme!r},
                        ),
                        padding="18px",
                        tone="featured",
                        theme={theme!r},
                    ),
                    widths=["50%", "50%"],
                    gap="14px",
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Pricing

            component = Pricing(
                plans={plans!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Grids":
        column_count = 4 if "4 columns" in title.lower() else 3
        widths = ["25%"] * 4 if column_count == 4 else ["34%", "33%", "33%"]
        column_code = []
        for index in range(column_count):
            column_code.append(
                f'Surface(Stack(Heading({_pick(headings, index, f"Column {index + 1}")!r}, level="small", theme={theme!r}), Text({_pick(paragraphs, index, f"Column {index + 1}")!r}, theme={theme!r}), gap="8px", theme={theme!r}), padding="16px", theme={theme!r})'
            )
        return dedent(
            f"""
            from pyzahidal import Columns, Heading, Stack, Surface, Text

            component = Stack(
                Heading({str(heading_text)!r}, level="small", theme={theme!r}),
                Columns(
                    {", ".join(column_code)},
                    widths={widths!r},
                    gap="12px",
                ),
                gap="10px",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Progress Bars":
        progress_value = 50
        percents = [str(value) for value in source.get("percents", []) if str(value).strip()]
        if percents:
            try:
                progress_value = int(float(percents[0].replace("%", "")))
            except ValueError:
                progress_value = 50
        return dedent(
            f"""
            from pyzahidal import ProgressBar, Stack, Text

            component = Stack(
                Text({str(heading_text)!r}, theme={theme!r}),
                ProgressBar({progress_value}, theme={theme!r}),
                Text({f"{progress_value}% complete"!r}, size="small", tone="muted", theme={theme!r}),
                gap="8px",
                theme={theme!r},
            )
            """
        ).strip()

    if category == "Headers":
        nav_items = [(str(link.get("label", f"Link {index + 1}")), str(link.get("href", "#"))) for index, link in enumerate(links[:5])]
        if len(images) > 1 and "social" in title.lower():
            social_items = [
                {"href": str(_pick(links, index, {"href": "#"}).get("href", "#")), "icon_src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", f"Social {index + 1}"))}
                for index, image in enumerate(images[1:5])
            ]
            return dedent(
                f"""
                from pyzahidal import Columns, Image, Inline, Link, Section, raw

                component = Section(
                    Columns(
                        Image({first_image_src!r}, alt={first_image_alt!r}, width="auto", block=False, styles={{"max-width": "180px", "border-radius": "0"}}, theme={theme!r}),
                        Inline(
                            *[
                                Link(
                                    raw(f'<img src="{{item["icon_src"]}}" alt="{{item["alt"]}}" style="display:block; width:20px; height:20px; margin:0 auto"/>'),
                                    href=item["href"],
                                    theme={theme!r},
                                    styles={{"display": "inline-block", "line-height": "1"}},
                                )
                                for item in {social_items!r}
                            ],
                            align="right",
                            gap="24px",
                            wrap=True,
                            theme={theme!r},
                        ),
                        widths=["58%", "42%"],
                        gap="16px",
                        vertical_align="middle",
                    ),
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Header

            component = Header(
                {str(heading_text)!r},
                nav_items={nav_items!r},
                logo_src={first_image_src!r},
                logo_alt={first_image_alt!r},
                tagline={str(body_text)!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Logos":
        logos = [
            {"label": str(image.get("alt", f"Logo {index + 1}")), "src": str(image.get("src", first_image_src))}
            for index, image in enumerate(images[:6])
        ]
        return dedent(
            f"""
            from pyzahidal import Heading, LogoStrip, Section, Stack, Text

            component = Section(
                Stack(
                    Heading({str(heading_text)!r}, level="small", align="center", theme={theme!r}),
                    LogoStrip(
                        items={logos!r},
                        columns={min(5, len(logos)) if logos else 5},
                        theme={theme!r},
                    ),
                    Text({str(body_text)!r}, size="small", tone="muted", align="center", theme={theme!r}),
                    gap="20px",
                    align="center",
                    theme={theme!r},
                ),
                padding="36px 24px",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Footers":
        social_items = [(str(link.get("label", f"Link {index + 1}")), str(link.get("href", "#"))) for index, link in enumerate(links[:5])]
        menu_items = [(str(link.get("label", f"Link {index + 1}")), str(link.get("href", "#"))) for index, link in enumerate(links[5:9])]
        legal_links = [(str(link.get("label", f"Link {index + 1}")), str(link.get("href", "#"))) for index, link in enumerate(links[9:13])]
        return dedent(
            f"""
            from pyzahidal import Footer

            component = Footer(
                {str(heading_text)!r},
                social_items={social_items!r},
                top_image_src={first_image_src!r},
                top_image_alt={first_image_alt!r},
                description={str(body_text)!r},
                menu_items={menu_items!r},
                legal_links={legal_links!r},
                disclaimer={str(_pick(paragraphs, 1, ""))!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "HERO":
        if layout in {"centered", "grid"} and source.get("layout_flags", {}).get("has_split_columns") is not True:
            image_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[:3]]
            return dedent(
                f"""
                from pyzahidal import Button, Heading, ImageGroup, Inline, Section, Stack, Stats, Text

                component = Section(
                    Stack(
                        Text({str(_pick(headings, 1, _pick(headings, 2, "Featured")))!r}, size="kicker", tone="accent", align="center", theme={theme!r}),
                        Heading({str(heading_text)!r}, level="hero", align="center", theme={theme!r}),
                        Text({str(body_text)!r}, align="center", tone="muted", theme={theme!r}),
                        Inline(
                            Button({str(primary_link.get("label", "Learn more"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                            Button({str(secondary_link.get("label", "Details"))!r}, href={str(secondary_link.get("href", "#"))!r}, variant="secondary", theme={theme!r}),
                            align="center",
                            gap="12px",
                            wrap=True,
                            theme={theme!r},
                        ),
                        ImageGroup(items={image_items!r}, columns={min(3, len(image_items)) or 1}, gap="10px", theme={theme!r}),
                        gap="14px",
                        align="center",
                        theme={theme!r},
                    ),
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Hero

            component = Hero(
                title={str(heading_text)!r},
                body={str(body_text)!r},
                primary_action={{"label": {str(primary_link.get("label", "Explore"))!r}, "href": {str(primary_link.get("href", "#"))!r}, "variant": "primary"}},
                secondary_action={{"label": {str(secondary_link.get("label", "Details"))!r}, "href": {str(secondary_link.get("href", "#"))!r}, "variant": "secondary"}},
                media={{"src": {first_image_src!r}, "alt": {first_image_alt!r}, "title": {str(_pick(headings, 1, heading_text))!r}, "body": {str(_pick(paragraphs, 1, body_text))!r}}},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Call to Action":
        actions = [
            {"label": str(primary_link.get("label", "Open")), "href": str(primary_link.get("href", "#")), "variant": "primary"},
            {"label": str(secondary_link.get("label", "Learn more")), "href": str(secondary_link.get("href", "#")), "variant": "secondary"},
        ]
        if images and layout == "grid":
            image_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[:3]]
            return dedent(
                f"""
                from pyzahidal import CallToAction, ImageGroup, Section, Stack

                component = Section(
                    Stack(
                        CallToAction({str(heading_text)!r}, {str(body_text)!r}, actions={actions!r}, theme={theme!r}),
                        ImageGroup(items={image_items!r}, columns={min(3, len(image_items)) or 1}, gap="10px", theme={theme!r}),
                        gap="14px",
                        theme={theme!r},
                    ),
                    theme={theme!r},
                )
                """
            ).strip()
        if images:
            return dedent(
                f"""
                from pyzahidal import CallToAction, Surface

                component = Surface(
                    CallToAction({str(heading_text)!r}, {str(body_text)!r}, actions={actions!r}, theme={theme!r}),
                    background_image={first_image_src!r},
                    background_color="#1f2937",
                    padding="24px",
                    radius="16px",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import CallToAction

            component = CallToAction(
                {str(heading_text)!r},
                {str(body_text)!r},
                actions={actions!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Coupons":
        return dedent(
            f"""
            from pyzahidal import Button, Heading, Section, Stack, Text

            component = Section(
                Stack(
                    Heading({str(heading_text)!r}, level="small", theme={theme!r}),
                    Text({str(body_text)!r}, theme={theme!r}),
                    Button({str(primary_link.get("label", "Shop now"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                    gap="10px",
                    theme={theme!r},
                ),
                padding="24px",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Bento grids":
        if "even split image stats" in title.lower():
            feature_image = str(images[-1].get("src", first_image_src)) if images else first_image_src
            stats_heading = str(_pick(headings, 0, "API Calls"))
            stats_value = str(_pick(paragraphs, 0, _pick(prices, 0, "25,000")))
            trend_text = str(_pick(table_headers, 1, "10% increase"))
            report_label = str(primary_link.get("label", "View report"))
            report_href = str(primary_link.get("href", "#"))
            metric_specs = [
                {"label": str(_pick(paragraphs, 2, "Engine v2")), "value": str(_pick(paragraphs, 3, "75x")), "detail": str(_pick(paragraphs, 4, "faster")), "background": "#f9fafb"},
                {"label": str(_pick(paragraphs, 5, "Cost reduction")), "value": str(_pick(percents, 0, "50%")), "detail": str(_pick(paragraphs, 4, "faster")), "background": "#f3f4f6"},
                {"label": str(_pick(paragraphs, 7, "Load time")), "value": str(_pick(paragraphs, 3, "75x")), "detail": str(_pick(paragraphs, 4, "faster")), "background": "#ffffff"},
            ]
            return dedent(
                f"""
                from pyzahidal import Columns, Heading, Image, Link, Section, Stack, Surface, Text

                component = Section(
                    Stack(
                        Columns(
                            Surface(
                                Stack(
                                    Heading({stats_heading!r}, level="small", theme={theme!r}),
                                    Text({stats_value!r}, theme={theme!r}, styles={{"font-size": "24px", "line-height": "32px", "font-weight": "700", "color": "#030712"}}),
                                    Text({trend_text!r}, size="small", tone="muted", theme={theme!r}),
                                    Link({report_label!r}, href={report_href!r}, theme={theme!r}, styles={{"font-size": "12px", "font-weight": "500", "color": "#4f46e5"}}),
                                    gap="10px",
                                    theme={theme!r},
                                ),
                                padding="16px",
                                tone="subtle",
                                radius="8px",
                                styles={{"background": "#f9fafb", "border": "1px solid #d1d5db", "box-shadow": "none"}},
                                theme={theme!r},
                            ),
                            Image({feature_image!r}, alt="", theme={theme!r}, styles={{"border-radius": "8px"}}),
                            widths=["50%", "50%"],
                            gap="24px",
                            vertical_align="middle",
                        ),
                        Columns(
                            {", ".join(
                                f'''Surface(Stack(Text({spec["label"]!r}, size="small", theme={theme!r}, styles={{"font-weight": "600", "color": "#030712", "text-align": "center"}}), Text({spec["value"]!r}, theme={theme!r}, styles={{"font-size": "48px", "line-height": "1.1", "font-weight": "500", "color": "#030712", "text-align": "center"}}), Text({spec["detail"]!r}, size="small", tone="muted", align="center", theme={theme!r}), gap="4px", align="center", theme={theme!r}), padding="56px 0", tone="subtle", radius="8px", styles={{"background": {spec["background"]!r}, "border": "0", "box-shadow": "none"}}, theme={theme!r})'''
                                for spec in metric_specs
                            )},
                            widths=["33%", "33%", "33%"],
                            gap="24px",
                            vertical_align="middle",
                        ),
                        gap="14px",
                        theme={theme!r},
                    ),
                    theme={theme!r},
                )
                """
            ).strip()
        items = []
        for index in range(max(3, min(4, len(headings)))):
            items.append(
                {
                    "eyebrow": str(_pick(headings, index + 1, "Highlight")),
                    "title": str(_pick(headings, index, f"Card {index + 1}")),
                    "body": str(_pick(paragraphs, index, body_text)),
                }
            )
        return dedent(
            f"""
            from pyzahidal import BentoGrid

            component = BentoGrid(
                items={items!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Feature":
        return dedent(
            f"""
            from pyzahidal import Button, Columns, Heading, ImageGroup, Stack, Surface, Text

            component = Columns(
                Surface(
                    Stack(
                        Heading({str(heading_text)!r}, level="small", theme={theme!r}),
                        Text({str(body_text)!r}, theme={theme!r}),
                        Button({str(primary_link.get("label", "Discover"))!r}, href={str(primary_link.get("href", "#"))!r}, variant="ghost", theme={theme!r}),
                        gap="10px",
                        theme={theme!r},
                    ),
                    padding="20px",
                    theme={theme!r},
                ),
                ImageGroup(
                    items={[{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[:2]]!r},
                    columns={min(2, max(1, len(images[:2])))},
                    gap="10px",
                    theme={theme!r},
                ),
                widths=["48%", "52%"],
                gap="16px",
            )
            """
        ).strip()
    if category == "Images":
        if len(images) > 1:
            image_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[: min(4, len(images))]]
            return dedent(
                f"""
                from pyzahidal import ImageGroup

                component = ImageGroup(
                    items={image_items!r},
                    columns={2 if layout in {"grid", "split"} else min(3, len(image_items))},
                    gap="10px",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Image

            component = Image(
                src={first_image_src!r},
                alt={first_image_alt!r},
                width="100%",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Stats":
        metrics = []
        values = [str(value) for value in source.get("percents", []) if str(value).strip()] + prices
        for index, value in enumerate((values or ["42%", "18%", "$12k"])[:3]):
            metrics.append({"label": str(_pick(headings, index, f"Metric {index + 1}")), "value": value, "detail": str(_pick(paragraphs, index, ""))})
        if images:
            return dedent(
                f"""
                from pyzahidal import Stats, Surface

                component = Surface(
                    Stats({metrics!r}, theme={theme!r}),
                    background_image={first_image_src!r},
                    background_color="#1f2937",
                    padding="22px",
                    radius="18px",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Stats

            component = Stats(
                {metrics!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Blog":
        card_total = max(2, min(3, len(headings) or len(images) or 2))
        card_code = []
        for index in range(card_total):
            card_code.append(
                f'''Surface(Stack(Image({str(_pick(images, index, {"src": first_image_src}).get("src", first_image_src))!r}, alt={str(_pick(images, index, {"alt": f"Post {index + 1}"}).get("alt", f"Post {index + 1}"))!r}, theme={theme!r}), Heading({str(_pick(headings, index, f"Post {index + 1}"))!r}, level="small", theme={theme!r}), Text({str(_pick(paragraphs, index, body_text))!r}, size="small", theme={theme!r}), Button({str(_pick(links, index, {"label": "Read more"}).get("label", "Read more"))!r}, href={str(_pick(links, index, {"href": "#"}).get("href", "#"))!r}, variant="ghost", theme={theme!r}), gap="10px", theme={theme!r}), padding="16px", theme={theme!r})'''
            )
        return dedent(
            f"""
            from pyzahidal import Button, Columns, Heading, Image, Stack, Surface, Text

            component = Columns(
                {", ".join(card_code)},
                widths={["34%", "33%", "33%"][:card_total]!r},
                gap="14px",
            )
            """
        ).strip()
    if category == "Content":
        return dedent(
            f"""
            from pyzahidal import Heading, Section, Stack, Text

            component = Section(
                Stack(
                    Text({str(_pick(headings, 1, "Content"))!r}, size="kicker", theme={theme!r}),
                    Heading({str(heading_text)!r}, level="section", theme={theme!r}),
                    Text({str(body_text)!r}, theme={theme!r}),
                    Text({str(_pick(paragraphs, 1, ""))!r}, size="small", tone="muted", theme={theme!r}),
                    gap="10px",
                    theme={theme!r},
                ),
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Social":
        if images:
            social_items = [{"href": str(_pick(links, index, {"href": "#"}).get("href", "#")), "icon_src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", f"Network {index + 1}"))} for index, image in enumerate(images[:5])]
            if "stacked" in title.lower() and "label" in title.lower():
                return dedent(
                    f"""
                    from pyzahidal import Heading, Inline, Link, Section, Stack, Text, raw

                    component = Section(
                        Stack(
                            Heading({str(_pick(headings, 0, "Connect with us"))!r}, level="small", align="center", theme={theme!r}),
                            Inline(
                                *[
                                    Link(
                                        raw(
                                            f'<span style="display:inline-block; text-align:center"><img src="{{item["icon_src"]}}" alt="{{item["alt"]}}" style="display:block; width:24px; height:24px; margin:0 auto"/><span style="display:block; height:4px; line-height:4px; font-size:4px"></span><span style="display:block">{{item["alt"]}}</span></span>'
                                        ),
                                        href=item["href"],
                                        theme={theme!r},
                                        styles={{"display": "inline-block", "text-align": "center", "font-size": "16px", "font-weight": "500", "color": "#6b7280"}},
                                    )
                                    for item in {social_items!r}
                                ],
                                align="center",
                                gap="36px",
                                wrap=True,
                                theme={theme!r},
                            ),
                            Text({str(_pick(paragraphs, 0, body_text))!r}, size="small", tone="muted", align="center", theme={theme!r}),
                            gap="14px",
                            align="center",
                            theme={theme!r},
                        ),
                        theme={theme!r},
                    )
                    """
                ).strip()
            return dedent(
                f"""
                from pyzahidal import Button, Heading, Inline, Section, SocialLinks, Stack, Text

                component = Section(
                    Stack(
                        Heading({str(_pick(headings, 0, "Connect with us"))!r}, level="small", align="center", theme={theme!r}),
                        Text({str(_pick(paragraphs, 0, body_text))!r}, size="small", tone="muted", align="center", theme={theme!r}),
                        SocialLinks({social_items!r}, mode="icon", theme={theme!r}),
                        Inline(
                            Button({str(primary_link.get("label", "Open"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                            Button({str(secondary_link.get("label", "Details"))!r}, href={str(secondary_link.get("href", "#"))!r}, variant="secondary", theme={theme!r}),
                            align="center",
                            gap="10px",
                            theme={theme!r},
                        ),
                        gap="14px",
                        align="center",
                        theme={theme!r},
                    ),
                    theme={theme!r},
                )
                """
            ).strip()
        items = [(str(link.get("label", f"Network {index + 1}")), str(link.get("href", "#"))) for index, link in enumerate(links[:5])]
        return dedent(
            f"""
            from pyzahidal import SocialLinks

            component = SocialLinks(
                items={items!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "FAQs":
        faq_items = []
        for index in range(max(2, min(4, len(headings) - 1))):
            faq_items.append((str(_pick(headings, index + 1, f"Question {index + 1}")), str(_pick(paragraphs, index, body_text))))
        return dedent(
            f"""
            from pyzahidal import FAQ

            component = FAQ(
                items={faq_items!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Team":
        members = []
        for index in range(max(2, min(4, len(headings)))):
            members.append(
                {
                    "name": str(_pick(headings, index, f"Member {index + 1}")),
                    "role": str(_pick(paragraphs, index, "Team")),
                    "image": str(_pick(images, index, {"src": first_image_src}).get("src", first_image_src)),
                }
            )
        if len(members) >= 3:
            member_code = []
            social_images = images[len(members) :]
            for index, member in enumerate(members[:3]):
                social_links = []
                for offset, link in enumerate(links[index * 3 : index * 3 + 3]):
                    if len(social_images) <= index * 3 + offset:
                        continue
                    social_links.append(
                        f'Link(raw(\'<img src="{str(social_images[index * 3 + offset].get("src", first_image_src))}" alt="{str(link.get("label", "social"))}" style="display:block; width:20px; height:20px; margin:0 auto"/>\'), href={str(link.get("href", "#"))!r}, theme={theme!r}, styles={{"display": "inline-block", "line-height": "1"}})'
                    )
                social_row = ""
                if social_links:
                    social_row = f', Spacer("8px"), Inline({", ".join(social_links)}, align="center", gap="16px", wrap=True, theme={theme!r})'
                member_code.append(
                    f'''Stack(Avatar({member["image"]!r}, alt={member["name"]!r}), Heading({member["name"]!r}, level="small", theme={theme!r}), Text({member["role"]!r}, size="small", tone="muted", theme={theme!r}){social_row}, gap="8px", align="center", theme={theme!r})'''
                )
            return dedent(
                f"""
                from pyzahidal import Avatar, Columns, Heading, Inline, Link, Spacer, Stack, Text, raw

                component = Columns(
                    {", ".join(member_code)},
                    widths=["33%", "33%", "33%"],
                    gap="12px",
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Team

            component = Team(
                members={members!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Testimonials":
        entries = []
        for index in range(max(2, min(3, len(paragraphs)))):
            entries.append({"quote": str(_pick(paragraphs, index, body_text)), "author": str(_pick(headings, index + 1, f"Person {index + 1}"))})
        if links:
            return dedent(
                f"""
                from pyzahidal import Button, Stack, Testimonials

                component = Stack(
                    Testimonials(items={entries!r}, theme={theme!r}),
                    Button({str(primary_link.get("label", "Read more"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                    align="center",
                    gap="12px",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Testimonials

            component = Testimonials(
                items={entries!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Timelines":
        steps = []
        versions = [str(value) for value in source.get("versions", []) if str(value).strip()]
        dates = [str(value) for value in source.get("dates", []) if str(value).strip()]
        for index in range(max(2, min(3, len(headings)))):
            steps.append(
                {
                    "version": str(_pick(versions, index, f"v1.0.{index}")),
                    "date": str(_pick(dates, index, "Jan")),
                    "category": str(_pick(headings, index, "Release")),
                    "title": str(_pick(headings, index + 1, f"Milestone {index + 1}")),
                    "detail": str(_pick(paragraphs, index, body_text)),
                }
            )
        return dedent(
            f"""
            from pyzahidal import Timeline

            component = Timeline(
                steps={steps!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Category Previews":
        card_titles = headings[1:] if len(headings) > 1 else [heading_text]
        price_candidates = [value for value in paragraphs if "$" in value]
        card_count = max(1, min(3, len(card_titles) or len(images) or 1))
        widths = ["34%", "33%", "33%"] if card_count == 3 else (["50%", "50%"] if card_count == 2 else None)
        card_code = []
        for index in range(card_count):
            card_code.append(
                f'''Surface(Stack(Image({str(_pick(images, index, {"src": first_image_src}).get("src", first_image_src))!r}, alt={str(_pick(images, index, {"alt": _pick(card_titles, index, "Category")}).get("alt", _pick(card_titles, index, "Category")))!r}, theme={theme!r}), Heading({str(_pick(card_titles, index, f"Category {index + 1}"))!r}, level="small", theme={theme!r}), Text({str(_pick(price_candidates, index, _pick(prices, index, "")))!r}, size="small", tone="muted", theme={theme!r}), Button({str(_pick(links, 0, {"label": "Shop now"}).get("label", "Shop now"))!r}, href={str(_pick(links, 0, {"href": "#"}).get("href", "#"))!r}, variant="secondary", theme={theme!r}), gap="10px", theme={theme!r}), padding="16px", theme={theme!r})'''
            )
        return dedent(
            f"""
            from pyzahidal import Button, Columns, Heading, Image, Section, Stack, Surface, Text

            component = Section(
                Stack(
                    Heading({str(_pick(headings, 0, heading_text))!r}, level="section", theme={theme!r}),
                    Text({str(_pick(paragraphs, 0, body_text))!r}, theme={theme!r}),
                    Columns(
                        {", ".join(card_code)},
                        widths={widths!r},
                        gap="14px",
                    ),
                    gap="14px",
                    theme={theme!r},
                ),
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Reviews":
        reviews = []
        for index in range(max(2, min(3, len(paragraphs)))):
            reviews.append({"quote": str(_pick(paragraphs, index, body_text)), "author": str(_pick(headings, index + 1, f"Reviewer {index + 1}")), "src": str(_pick(images, index, {"src": first_image_src}).get("src", first_image_src))})
        return dedent(
            f"""
            from pyzahidal import Reviews

            component = Reviews(
                items={reviews!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Order Summary":
        summary_rows = []
        for row in table_rows[:6]:
            if len(row) >= 2:
                summary_rows.append((row[0], row[-1]))
        if not summary_rows:
            summary_rows = [("Subtotal", str(_pick(prices, 0, "$0"))), ("Total", str(_pick(prices, 1, _pick(prices, 0, "$0"))))]
        progress_value = None
        percents = [str(value) for value in source.get("percents", []) if str(value).strip()]
        if percents:
            try:
                progress_value = int(float(percents[0].replace("%", "")))
            except ValueError:
                progress_value = None
        if images:
            image_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", ""))} for image in images[:2]]
            return dedent(
                f"""
                from pyzahidal import ImageGroup, OrderSummary, Stack

                component = Stack(
                    OrderSummary(rows={summary_rows!r}, progress={progress_value!r}, theme={theme!r}),
                    ImageGroup(items={image_items!r}, columns={min(2, len(image_items)) or 1}, gap="10px", theme={theme!r}),
                    gap="14px",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import OrderSummary

            component = OrderSummary(
                rows={summary_rows!r},
                progress={progress_value!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Containers":
        return dedent(
            f"""
            from pyzahidal import Container, Stack, Text

            component = Container(
                Stack(
                    Text({str(heading_text)!r}, size="kicker", theme={theme!r}),
                    Text({str(body_text)!r}, theme={theme!r}),
                    gap="8px",
                    theme={theme!r},
                ),
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Spacing":
        if "divider" in title.lower() and images:
            social_items = [{"href": "#", "icon_src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", f"Social {index + 1}"))} for index, image in enumerate(images[:5])]
            return dedent(
                f"""
                from pyzahidal import Columns, Divider, Inline, Link, raw

                component = Columns(
                    Divider(theme={theme!r}),
                    Inline(
                        *[
                            Link(
                                raw(f'<img src="{{item["icon_src"]}}" alt="{{item["alt"]}}" style="display:block; width:20px; height:20px; margin:0 auto"/>'),
                                href=item["href"],
                                theme={theme!r},
                                styles={{"display": "inline-block", "line-height": "1"}},
                            )
                            for item in {social_items[:4]!r}
                        ],
                        align="center",
                        gap="16px",
                        wrap=True,
                        theme={theme!r},
                    ),
                    Divider(theme={theme!r}),
                    widths=["39%", "22%", "39%"],
                    gap="12px",
                    vertical_align="middle",
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Spacer, Stack, Text

            component = Stack(
                Text({str(heading_text)!r}, theme={theme!r}),
                Spacer("32px"),
                Text({str(body_text)!r}, theme={theme!r}),
                gap="0",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Buttons":
        if links:
            button_code = []
            for index, link in enumerate(links[: min(5, len(images) or len(links))]):
                icon_src = str(images[index].get("src", first_image_src)) if index < len(images) else first_image_src
                icon_alt = str(images[index].get("alt", "")) if index < len(images) else ""
                button_code.append(
                    f'''Button({str(link.get("label", f"Action {index + 1}"))!r}, href={str(link.get("href", "#"))!r}, icon_src={icon_src!r}, icon_alt={icon_alt!r}, variant={"primary" if index == 0 else "secondary"!r}, theme={theme!r})'''
                )
            return dedent(
                f"""
                from pyzahidal import Button, Inline

                component = Inline(
                    {", ".join(button_code)},
                    gap="10px",
                    theme={theme!r},
                )
                """
            ).strip()
        icon_src = str(_pick(images, 0, {"src": first_image_src}).get("src", first_image_src))
        return dedent(
            f"""
            from pyzahidal import Button

            component = Button(
                {str(primary_link.get("label", "Open"))!r},
                href={str(primary_link.get("href", "#"))!r},
                icon_src={icon_src!r},
                icon_alt={str(_pick(images, 0, {"alt": "icon"}).get("alt", "icon"))!r},
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Pills":
        labels = [str(_pick(headings, 0, "Healthy")), str(_pick(headings, 1, "Pending")), str(_pick(headings, 2, "Blocked"))]
        return dedent(
            f"""
            from pyzahidal import Inline, Pill

            component = Inline(
                Pill({labels[0]!r}, tone="success", theme={theme!r}),
                Pill({labels[1]!r}, tone="warning", theme={theme!r}),
                Pill({labels[2]!r}, tone="danger", theme={theme!r}),
                gap="8px",
                theme={theme!r},
            )
            """
        ).strip()
    if category == "Avatars":
        if len(images) > 1:
            avatar_items = [{"src": str(image.get("src", first_image_src)), "alt": str(image.get("alt", f"Avatar {index + 1}"))} for index, image in enumerate(images[:5])]
            return dedent(
                f"""
                from pyzahidal import AvatarGroup, Stack, Text

                component = Stack(
                    AvatarGroup({avatar_items!r}, size="52px", overlap="16px", theme={theme!r}),
                    Text({str(body_text)!r}, size="small", tone="muted", align="center", theme={theme!r}),
                    gap="12px",
                    align="center",
                    theme={theme!r},
                )
                """
            ).strip()
        return dedent(
            f"""
            from pyzahidal import Avatar

            component = Avatar(
                src={first_image_src!r},
                alt={first_image_alt!r},
                size="56px",
                theme={theme!r},
            )
            """
        ).strip()
    return dedent(
        f"""
        from pyzahidal import Button, Heading, Section, Stack, Text

        component = Section(
            Stack(
                Heading({str(heading_text)!r}, level="small", theme={theme!r}),
                Text({str(body_text)!r}, theme={theme!r}),
                Button({str(primary_link.get("label", "Learn more"))!r}, href={str(primary_link.get("href", "#"))!r}, theme={theme!r}),
                gap="10px",
                theme={theme!r},
            ),
            theme={theme!r},
        )
        """
    ).strip()


def _group_to_card(group: dict[str, object], theme: str, *, compact: bool = False) -> object:
    heading = str(group.get("heading", "")).strip()
    paragraphs = [str(value).strip() for value in group.get("paragraphs", []) if str(value).strip()]
    children: list[object] = []
    if heading:
        children.append(ui.Heading(heading, level="small" if compact else "subsection", theme=theme))
    for index, paragraph in enumerate(paragraphs):
        if children:
            children.append(ui.Spacer("6px" if compact else "8px"))
        children.append(ui.Text(paragraph, size="small" if compact else "body", tone="muted" if index else "default", theme=theme))
    return ui.Surface(ui.Stack(*children, gap="0", theme=theme), padding="16px" if compact else "18px", tone="subtle", theme=theme)


def _render_image_strip(images: Sequence[dict[str, object]], theme: str, *, max_items: int = 3, columns: int | None = None) -> object:
    selected = list(images[:max_items])
    if not selected:
        return ""
    return ui.ImageGroup(
        items=[_image_spec(str(item.get("src", "")), alt=str(item.get("alt", ""))) for item in selected],
        columns=columns or min(len(selected), 3),
        gap="10px",
        theme=theme,
    )


def _source_layout(source: dict[str, object]) -> str:
    return str(source.get("layout", "list"))


def _source_flags(source: dict[str, object]) -> dict[str, object]:
    return dict(source.get("layout_flags", {}))


def _source_groups(source: dict[str, object]) -> list[dict[str, object]]:
    return [value for value in source.get("groups", []) if isinstance(value, dict)]


def _first_descriptive_paragraph(paragraphs: Sequence[str], *excluded: str) -> str:
    excluded_normalized = {_normalize_whitespace(value) for value in excluded if value}
    for paragraph in paragraphs:
        normalized = _normalize_whitespace(paragraph)
        if not normalized or normalized in excluded_normalized:
            continue
        return paragraph
    return paragraphs[0] if paragraphs else ""


def _render_curated_source_preview(source_html: str, title: str) -> str:
    body = source_html if "<html" in source_html.lower() else (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"/>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>"
        f"<title>{escape(title)}</title></head><body>{source_html}</body></html>"
    )
    if "<body" in body.lower():
        return body
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"/>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>"
        f"<title>{escape(title)}</title></head><body>{source_html}</body></html>"
    )


def curated_examples(output_root: Path = ROOT / "docs") -> list[CuratedExampleSpec]:
    _ = output_root
    return _legacy_curated_examples()


def make_inventory() -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for name in canonical_names():
        spec = EXAMPLES[name]
        example_path = f"assets/examples/{spec.slug}.html"
        screenshot_path = f"assets/screenshots/{spec.slug}.png"
        inventory.append(
            {
                "name": name,
                "kind": "api",
                "group": GROUPS[name],
                "signature": signature_for(name),
                "description": DESCRIPTION_BY_NAME[name],
                "aliases": aliases_for(name),
                "example_slug": spec.slug,
                "example_path": example_path,
                "screenshot_path": screenshot_path,
                "options": option_lines(name),
                "notes": SPECIAL_NOTES.get(name, []),
            }
        )
    return inventory


def make_curated_inventory(specs: list[CuratedExampleSpec]) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for spec in specs:
        inventory.append(
            {
                "name": spec.title,
                "kind": "curated_example",
                "group": "examples",
                "category": spec.category,
                "signature": "Curated source-inspired example",
                "description": spec.description,
                "aliases": [],
                "example_slug": spec.slug,
                "example_path": curated_showcase_path(spec.slug),
                "screenshot_path": spec.screenshot_path,
                "options": [],
                "notes": [],
            }
        )
    return inventory


CURATED_PARITY_THRESHOLD = 0.66


def _curated_word_set(html: str) -> set[str]:
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return {word for word in re.findall(r"[a-z0-9%$'.-]+", text) if len(word) > 2}


def _ratio_similarity(actual: int, expected: int) -> float:
    if actual == expected == 0:
        return 1.0
    return min(actual, expected) / max(actual, expected, 1)


def _curated_structural_metrics(source_data: dict[str, object], generated_html: str) -> dict[str, object]:
    generated_data = _extract_source_data(generated_html, None)
    source_flags = _source_flags(source_data)
    generated_flags = _source_flags(generated_data)
    source_words = _curated_word_set(str(source_data.get("source_html", "")))
    generated_words = _curated_word_set(generated_html)
    content_overlap = len(source_words & generated_words) / max(1, len(source_words | generated_words))
    source_layout = _source_layout(source_data)
    generated_layout = _source_layout(generated_data)
    if source_layout == generated_layout:
        layout_match = 1.0
    elif {source_layout, generated_layout} in ({"split", "grid"}, {"table", "split"}, {"table", "grid"}, {"centered", "list"}):
        layout_match = 0.65
    elif "table" in {source_layout, generated_layout} and {"split", "grid", "list"} & {source_layout, generated_layout}:
        layout_match = 0.45
    else:
        layout_match = 0.25
    image_similarity = _ratio_similarity(len(source_data.get("images", [])), len(generated_data.get("images", [])))
    link_similarity = _ratio_similarity(len(source_data.get("links", [])), len(generated_data.get("links", [])))
    card_similarity = _ratio_similarity(int(source_flags.get("card_count", 0)), int(generated_flags.get("card_count", 0)))
    table_similarity = _ratio_similarity(int(source_flags.get("table_rows", 0)), int(generated_flags.get("table_rows", 0)))
    button_similarity = _ratio_similarity(int(source_flags.get("button_count", 0)), int(generated_flags.get("button_count", 0)))
    score = (
        content_overlap * 0.3
        + layout_match * 0.2
        + image_similarity * 0.12
        + link_similarity * 0.12
        + card_similarity * 0.11
        + table_similarity * 0.05
        + button_similarity * 0.1
    )
    return {
        "generated_data": generated_data,
        "content_overlap": round(content_overlap, 4),
        "layout_match": round(layout_match, 4),
        "image_similarity": round(image_similarity, 4),
        "link_similarity": round(link_similarity, 4),
        "card_similarity": round(card_similarity, 4),
        "table_similarity": round(table_similarity, 4),
        "button_similarity": round(button_similarity, 4),
        "score": round(score, 4),
    }


def make_curated_mismatch_report(specs: list[CuratedExampleSpec], output_root: Path) -> dict[str, object]:
    section_map = load_curated_section_map()
    entries: list[dict[str, object]] = []
    for spec in specs:
        source_entry = section_map.get((spec.category, spec.title))
        source_html = str(source_entry.get("section", {}).get("iframeHtml", "")) if source_entry else ""
        source_data = _extract_source_data(source_html, None) if source_html else {}
        expected_markers = _curated_expected_markers(spec.category, source_data) if source_data else []

        preview_path = output_root / curated_showcase_path(spec.slug)
        generated_html = preview_path.read_text(encoding="utf-8") if preview_path.exists() else ""
        generated_html_lower = generated_html.lower()
        generated_text = _normalize_whitespace(_strip_html(generated_html)).lower()
        structural_metrics = _curated_structural_metrics(source_data, generated_html) if source_data and generated_html else {"score": 0.0}

        matched: list[str] = []
        missing: list[str] = []
        for marker in expected_markers:
            lowered = marker.lower()
            if lowered in generated_text or lowered in generated_html_lower:
                matched.append(marker)
            else:
                missing.append(marker)
        semantic_score = 1.0 if not expected_markers else len(matched) / len(expected_markers)
        score = semantic_score * 0.45 + float(structural_metrics["score"]) * 0.55
        passed = score >= CURATED_PARITY_THRESHOLD
        entries.append(
            {
                "category": spec.category,
                "title": spec.title,
                "slug": spec.slug,
                "example_path": curated_showcase_path(spec.slug),
                "source_url": spec.page_url,
                "source_example_path": spec.source_example_path,
                "source_screenshot_path": spec.source_screenshot_path,
                "visual_diff_path": spec.visual_diff_path,
                "expected_markers": expected_markers,
                "matched_markers": matched,
                "missing_markers": missing,
                "semantic_score": round(semantic_score, 4),
                "structural_score": structural_metrics["score"],
                "content_overlap": structural_metrics.get("content_overlap"),
                "layout_match": structural_metrics.get("layout_match"),
                "image_similarity": structural_metrics.get("image_similarity"),
                "link_similarity": structural_metrics.get("link_similarity"),
                "card_similarity": structural_metrics.get("card_similarity"),
                "table_similarity": structural_metrics.get("table_similarity"),
                "button_similarity": structural_metrics.get("button_similarity"),
                "score": round(score, 4),
                "pass": passed,
            }
        )

    failing = [entry for entry in entries if not entry["pass"]]
    average_score = sum(float(entry["score"]) for entry in entries) / max(1, len(entries))
    return {
        "threshold": CURATED_PARITY_THRESHOLD,
        "summary": {
            "total_examples": len(entries),
            "passing_examples": len(entries) - len(failing),
            "failing_examples": len(failing),
            "average_score": round(average_score, 4),
        },
        "failing": [{"category": entry["category"], "title": entry["title"], "score": entry["score"], "missing_markers": entry["missing_markers"]} for entry in failing],
        "entries": entries,
    }


def build_components_page(entries: list[dict[str, object]]) -> str:
    lines = [
        "# Components",
        "",
        "Use this page when you already know the building block you want. If you are new to the library, start with [Quickstart](../quickstart.md) or browse [Examples](examples.md) by use case first.",
        "",
    ]
    for group in ("document", "primitives", "sections"):
        group_entries = [entry for entry in entries if entry["group"] == group]
        if not group_entries:
            continue
        lines.extend([f"## {GROUP_TITLES[group]}", ""])
        for entry in group_entries:
            name = entry["name"]
            spec = EXAMPLES[name]
            preview_html = render_component_preview(
                spec.factory(),
                name,
                spec.description,
                preview_theme=infer_preview_theme(spec.code),
            )
            lines.extend(
                [
                    f"### `{name}`",
                    "",
                    entry["description"],
                    "",
                    "Best for: custom composition when you want direct control over the rendered building block.",
                    "",
                    f"Signature: `{entry['signature']}`",
                    "",
                ]
            )
            aliases = entry["aliases"]
            if aliases:
                lines.extend([f"Aliases: {', '.join(f'`{alias}`' for alias in aliases)}", ""])
            lines.extend(["See also: [Quickstart](../quickstart.md), [Examples](examples.md), [Themes](themes.md)", ""])
            lines.extend(["Options:", ""])
            lines.extend([f"- {line}" for line in entry["options"]])
            if entry["notes"]:
                lines.extend(["", "Notes:", ""])
                lines.extend([f"- {note}" for note in entry["notes"]])
            lines.extend(
                [
                    "",
                    "Code:",
                    "",
                    "```python",
                    spec.code,
                    "```",
                    "",
                    "Rendered result:",
                    "",
                    iframe(preview_html, entry["example_path"], f"{name} preview", example_height(name), page_depth=2),
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def build_templates_page(entries: list[dict[str, object]]) -> str:
    lines = [
        "# Templates",
        "",
        "Starter templates compose lower-level primitives and sections into opinionated email flows. Choose these when you want a working email quickly, then customize only the parts that differ.",
        "",
    ]
    for entry in [entry for entry in entries if entry["group"] == "templates"]:
        name = entry["name"]
        spec = EXAMPLES[name]
        preview_html = render_component_preview(
            spec.factory(),
            name,
            spec.description,
            preview_theme=infer_preview_theme(spec.code),
        )
        lines.extend(
            [
                f"## `{name}`",
                "",
                entry["description"],
                "",
                "Best for: getting to a complete email layout with the fewest decisions up front.",
                "",
                f"Signature: `{entry['signature']}`",
                "",
                "See also: [Quickstart](../quickstart.md), [Examples](examples.md), [Components](components.md)",
                "",
                "Options:",
                "",
            ]
        )
        lines.extend([f"- {line}" for line in entry["options"]])
        if entry["notes"]:
            lines.extend(["", "Notes:", ""])
            lines.extend([f"- {note}" for note in entry["notes"]])
        lines.extend(
            [
                "",
                "Code:",
                "",
                "```python",
                spec.code,
                "```",
                "",
                "Rendered result:",
                "",
                iframe(preview_html, entry["example_path"], f"{name} preview", example_height(name), page_depth=2),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def theme_token_table(theme_name: str) -> str:
    theme = ui.THEMES[theme_name]
    rows = ["| Token | Value |", "| --- | --- |"]
    for token in ("body_background", "surface_color", "hero_accent_background", "text_color", "heading_color", "primary_color", "secondary_color", "radius_md", "button_radius"):
        rows.append(f"| `{token}` | `{theme[token]}` |")
    return "\n".join(rows)


def build_themes_page(entries: list[dict[str, object]]) -> str:
    lines = [
        "# Themes",
        "",
        "Theme presets are plain token dictionaries consumed by `build_theme()` and by the themed component constructors.",
        "",
        "Available presets:",
        "",
    ]
    for theme_name in ui.THEMES:
        lines.extend([f"- `{theme_name}`: {THEME_DESCRIPTIONS.get(theme_name, 'Theme preset.') }"])
    lines.extend(["", "## Preset Tokens", ""])
    for theme_name in ui.THEMES:
        lines.extend([f"### `{theme_name}`", "", theme_token_table(theme_name), ""])
    lines.extend(["## Showcase", "", "These examples compare a few representative components across `default`, `editorial`, and `vibrant`.", ""])
    for component_name in ("Hero", "Button", "Pricing", "MarketingTemplate"):
        lines.extend([f"### `{component_name}` across themes", ""])
        for theme_name in ("default", "editorial", "vibrant"):
            slug = f"theme-{component_name.lower()}-{theme_name}"
            example_path = f"assets/examples/{slug}.html"
            component = THEME_SHOWCASES[component_name](theme_name)
            preview_html = render_component_preview(
                component,
                f"{component_name} {theme_name}",
                f"{component_name} rendered with the {theme_name} theme.",
                preview_theme=theme_name,
            )
            lines.extend(
                [
                    f"#### `{theme_name}`",
                    "",
                    iframe(preview_html, example_path, f"{component_name} {theme_name}", example_height(component_name), page_depth=2),
                    "",
                ]
            )
    lines.extend(
        [
            "## Overrides",
            "",
            "Use a preset name when you want the built-in token set, or pass `theme_overrides` to change just the tokens you need.",
            "",
            "```python",
            "from pyzahidal import Hero",
            "",
            "component = Hero(",
            '    eyebrow="Launch week",',
            '    title="Custom token override",',
            '    body="Keep the preset and change only the pieces you need.",',
            '    primary_action={"label": "View example", "href": "#", "variant": "primary"},',
            '    theme="editorial",',
            '    theme_overrides={"primary_color": "#0f766e", "button_radius": "6px"},',
            ")",
            "```",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_examples_page(specs: list[CuratedExampleSpec]) -> str:
    lines = [
        "# Examples",
        "",
        "These examples are curated static compositions built from real `pyzahidal` components.",
        "",
        "Use this page when you know the outcome you want, but not yet the exact component or template name.",
        "",
        "Best next steps:",
        "",
        "- Start with the track that matches your email goal.",
        "- Copy the example code that is closest to your target layout.",
        "- Follow the links to [Templates](templates.md), [Components](components.md), or [Themes](themes.md) when you need to go deeper.",
        "",
    ]
    grouped: dict[str, list[CuratedExampleSpec]] = {}
    for spec in specs:
        track_title, _ = example_track_for_category(spec.category)
        grouped.setdefault(track_title, []).append(spec)
    track_descriptions = {title: description for title, description, _ in EXAMPLE_TRACKS}
    ordered_tracks = [title for title, _, _ in EXAMPLE_TRACKS if title in grouped]
    for track_title in ordered_tracks:
        lines.extend([f"## {track_title}", "", track_descriptions[track_title], ""])
        for spec in grouped[track_title]:
            preview_html = render_component_preview(
                spec.factory(),
                spec.title,
                spec.description,
                preview_theme=spec.theme,
            )
            lines.extend(
                [
                    f"### `{spec.title}`",
                    "",
                    f"Category: `{spec.category}`",
                    "",
                    spec.description,
                    "",
                    "Use this when:",
                    "",
                    f"- You want a `{spec.category}`-style layout with real component code you can adapt.",
                    f"- You want a concrete preview before choosing between templates and lower-level components.",
                    "",
                    "Related docs:",
                    "",
                    "- [Templates](templates.md)",
                    "- [Components](components.md)",
                    "- [Themes](themes.md)",
                    "",
                    "Code:",
                    "",
                    "```python",
                    spec.code,
                    "```",
                    "",
                    "Rendered result:",
                    "",
                    iframe(preview_html, curated_showcase_path(spec.slug), f"{spec.title} preview", 940, page_depth=2),
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def build_index_page(entries: list[dict[str, object]]) -> str:
    component_count = len([entry for entry in entries if entry["group"] in {"document", "primitives", "sections"}])
    template_count = len([entry for entry in entries if entry["group"] == "templates"])
    example_count = len([entry for entry in entries if entry.get("kind") == "curated_example"])
    alias_count = len(ALIASES)
    lines = [
        "# pyzahidal Docs",
        "",
        "Browsable documentation for the public component library, starter templates, and theme presets.",
        "",
        "## What is covered",
        "",
        f"- `{component_count}` documented components, including the document shell.",
        f"- `{template_count}` starter templates.",
        f"- `{example_count}` generated curated gallery examples.",
        f"- `{len(ui.THEMES)}` built-in theme presets.",
        f"- `{alias_count}` exported aliases mapped back to their canonical components.",
        "",
        "## How to regenerate",
        "",
        "```bash",
        "python -m scripts.docs",
        "```",
        "",
        "## Theme Gallery",
        "",
        "A few representative examples rendered across multiple presets:",
        "",
    ]
    for component_name in ("Hero", "Button", "Pricing"):
        lines.extend([f"### `{component_name}`", ""])
        for theme_name in ("default", "editorial", "vibrant"):
            slug = f"theme-{component_name.lower()}-{theme_name}"
            component = THEME_SHOWCASES[component_name](theme_name)
            preview_html = render_component_preview(
                component,
                f"{component_name} {theme_name}",
                f"{component_name} rendered with the {theme_name} theme.",
                preview_theme=theme_name,
            )
            lines.extend(
                [
                    f"#### `{theme_name}`",
                    "",
                    iframe(preview_html, f"assets/examples/{slug}.html", f"{component_name} {theme_name}", example_height(component_name)),
                    "",
                ]
            )
    lines.extend(
        [
            "## Notes",
            "",
            "- Live previews are generated from real component constructors.",
            "- The generated pages under `docs/generated/` should be treated as build artifacts from the source scripts.",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def generate_theme_showcase_assets(examples_dir: Path) -> None:
    for component_name, factory in THEME_SHOWCASES.items():
        for theme_name in ("default", "editorial", "vibrant"):
            component = factory(theme_name)
            html = render_component_preview(component, f"{component_name} {theme_name}", f"{component_name} rendered with the {theme_name} theme.", preview_theme=theme_name)
            write_file(examples_dir / f"theme-{component_name.lower()}-{theme_name}.html", html)


def clean_curated_outputs(output_root: Path, specs: list[CuratedExampleSpec]) -> None:
    examples_dir = output_root / "assets" / "examples"
    source_examples_dir = output_root / "assets" / "examples-source"
    expected = {f"{spec.slug}.html" for spec in specs}
    for path in examples_dir.glob("curated-*.html"):
        if path.name not in expected:
            path.unlink(missing_ok=True)
    if source_examples_dir.exists():
        for path in source_examples_dir.glob("curated-*.html"):
            if path.name not in expected:
                path.unlink(missing_ok=True)


def generate(output_root: Path = ROOT / "docs") -> list[dict[str, object]]:
    generated_dir = output_root / "generated"
    examples_dir = output_root / "assets" / "examples"
    generated_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    inventory = make_inventory()
    for entry in inventory:
        name = entry["name"]
        spec = EXAMPLES[name]
        component = spec.factory()
        html = render_component_preview(component, name, spec.description, preview_theme=infer_preview_theme(spec.code))
        write_file(examples_dir / f"{spec.slug}.html", html)

    curated_specs = curated_examples(output_root=output_root)
    clean_curated_outputs(output_root, curated_specs)
    for spec in curated_specs:
        html = render_component_preview(
            spec.factory(),
            spec.title,
            spec.description,
            preview_theme=spec.theme,
        )
        write_file(examples_dir / f"{spec.slug}.html", html)
    curated_inventory = make_curated_inventory(curated_specs)

    generate_theme_showcase_assets(examples_dir)

    full_inventory = inventory + curated_inventory
    write_file(generated_dir / "components.md", build_components_page(inventory))
    write_file(generated_dir / "examples.md", build_examples_page(curated_specs))
    write_file(generated_dir / "templates.md", build_templates_page(inventory))
    write_file(generated_dir / "themes.md", build_themes_page(inventory))
    write_file(generated_dir / "api-inventory.json", json.dumps(full_inventory, indent=2))
    return full_inventory


def main() -> int:
    inventory = generate()
    print(f"Generated docs for {len(inventory)} public items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
