from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence, TypeVar

from .rendering import attrs_to_html, raw, render_fragment, render_tag
from .theme import build_theme


class Renderable:
    def render(self) -> str:
        raise NotImplementedError

    def render_template(self) -> str:
        return self.render()


@dataclass(frozen=True)
class ComponentSpec:
    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        return None


@dataclass(frozen=True)
class ActionSpec(ComponentSpec):
    label: str
    href: str = "#"
    variant: str = "primary"


@dataclass(frozen=True)
class ImageSpec(ComponentSpec):
    src: str
    alt: str = ""


@dataclass(frozen=True)
class AvatarSpec(ComponentSpec):
    src: str
    alt: str = ""
    name: str = ""


@dataclass(frozen=True)
class MenuItemSpec(ComponentSpec):
    label: str
    href: str = "#"


@dataclass(frozen=True)
class SocialLinkSpec(ComponentSpec):
    href: str = "#"
    label: str = ""
    icon_src: str = ""
    alt: str = ""


@dataclass(frozen=True)
class LogoSpec(ComponentSpec):
    label: str
    src: str = ""


@dataclass(frozen=True)
class MetricSpec(ComponentSpec):
    label: str
    value: object
    detail: object | None = None
    trend: str | None = None


@dataclass(frozen=True)
class DataColumnSpec(ComponentSpec):
    key: str
    header: object
    width: str = ""
    align: str = "left"


@dataclass(frozen=True)
class HeroMediaSpec(ImageSpec):
    eyebrow: str = "Preview"
    title: str = "Designed for campaigns"
    body: str = "A framed screenshot, mockup, or product visual."


@dataclass(frozen=True)
class BentoItemSpec(ComponentSpec):
    title: str
    body: str
    eyebrow: str = "Highlight"


@dataclass(frozen=True)
class BlogPostSpec(ComponentSpec):
    title: str
    excerpt: str
    href: str = "#"
    eyebrow: str = "Story"
    label: str = "Read more"


@dataclass(frozen=True)
class FaqItemSpec(ComponentSpec):
    question: str
    answer: str


@dataclass(frozen=True)
class TeamMemberSpec(ComponentSpec):
    name: str = ""
    role: str = ""
    image: str = ""
    bio: str = "Owns a critical slice of the campaign experience."
    meta: str = ""
    action: ActionSpec | None = None


@dataclass(frozen=True)
class TimelineStepSpec(ComponentSpec):
    version: str
    date: str
    category: str
    title: str
    detail: str


@dataclass(frozen=True)
class PricingPlanSpec(ComponentSpec):
    name: str
    price: str
    description: str
    features: Sequence[str] = ()
    action: ActionSpec = field(default_factory=lambda: ActionSpec("Choose plan"))
    badge: str | None = None
    featured: bool = False

    def validate(self) -> None:
        object.__setattr__(self, "features", tuple(self.features))


@dataclass(frozen=True)
class ProductSpec(ComponentSpec):
    name: str
    price: str
    description: str
    image_src: str = ""
    href: str = "#"
    label: str = "View product"
    badge: str = ""
    rating: str = ""
    reviews: str = ""
    action: ActionSpec | None = None
    features: Sequence[str] = ()

    def validate(self) -> None:
        object.__setattr__(self, "features", tuple(self.features))


@dataclass(frozen=True)
class ReviewSpec(ComponentSpec):
    quote: str = ""
    author: str = "Customer"
    role: str = "Customer"
    rating: str = ""
    src: str = ""
    action: ActionSpec | None = None


@dataclass(frozen=True)
class TestimonialSpec(ComponentSpec):
    quote: str
    author: str
    role: str = "Customer"


@dataclass(frozen=True)
class CartItemSpec(ComponentSpec):
    name: str
    qty: str
    price: str


SpecT = TypeVar("SpecT", bound=ComponentSpec)


def require_spec(value: object, expected_type: type[SpecT], field_name: str) -> SpecT:
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be {expected_type.__name__}, got {type(value).__name__}")
    return value


def require_spec_sequence(values: Sequence[object], expected_type: type[SpecT], field_name: str) -> list[SpecT]:
    normalized: list[SpecT] = []
    for index, value in enumerate(values, start=1):
        normalized.append(require_spec(value, expected_type, f"{field_name}[{index}]"))
    return normalized


@dataclass
class Component(Renderable):
    tag: str = "div"
    children: list[object] = field(default_factory=list)
    attrs: dict[str, object] = field(default_factory=dict)
    styles: dict[str, object] = field(default_factory=dict)
    default_styles: dict[str, object] = field(default_factory=dict)

    def __init__(
        self,
        *children: object,
        attrs: dict[str, object] | None = None,
        styles: dict[str, object] | None = None,
        **extra_attrs: object,
    ) -> None:
        self.children = list(children)
        self.attrs = attrs.copy() if attrs else {}
        self.attrs.update(extra_attrs)
        self.styles = styles.copy() if styles else {}
        self.default_styles = getattr(self, "default_styles", {}).copy()

    def render(self) -> str:
        merged_styles = {**self.default_styles, **self.styles}
        return render_tag(self.tag, attrs=self.attrs, styles=merged_styles, children=self.children)

    def render_template(self) -> str:
        merged_styles = {**self.default_styles, **self.styles}
        return render_tag(
            self.tag,
            attrs=self.attrs,
            styles=merged_styles,
            children=self.children,
            template_mode=True,
        )


@dataclass
class EmailDocument(Renderable):
    sections: Sequence[Renderable | str]
    preview_text: str = ""
    theme: str | dict[str, object] | None = None
    theme_overrides: dict[str, object] | None = None
    lang: str = "en"
    title: str = "Email"

    def render(self) -> str:
        return self._render(template_mode=False)

    def render_template(self) -> str:
        return self._render(template_mode=True)

    def _render(self, *, template_mode: bool) -> str:
        theme = build_theme(self.theme, self.theme_overrides)
        section_gap = theme["section_gap"]
        section_markup = "".join(
            render_tag(
                "tr",
                children=[
                    render_tag(
                        "td",
                        styles={"padding": f"0 0 {section_gap} 0"},
                        children=[section],
                        template_mode=template_mode,
                    )
                ],
                template_mode=template_mode,
            )
            for section in self.sections
        )
        body_table = render_tag(
            "table",
            attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
            styles={
                "max-width": theme["container_width"],
                "margin": "0 auto",
                "width": "100%",
            },
            children=[raw(section_markup)],
            template_mode=template_mode,
        )
        frame = render_tag(
            "table",
            attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
            styles={
                "max-width": f"calc({theme['container_width']} + 48px)",
                "margin": "0 auto",
                "width": "100%",
            },
            children=[
                raw(
                    render_tag(
                        "tr",
                        children=[
                            render_tag(
                                "td",
                                styles={
                                    "padding": "12px",
                                    "border": f"1px solid {theme['border_color']}",
                                    "border-radius": theme["radius_lg"],
                                    "background": theme["hero_accent_background"],
                                },
                                children=[raw(body_table)],
                                template_mode=template_mode,
                            )
                        ],
                        template_mode=template_mode,
                    )
                )
            ],
            template_mode=template_mode,
        )
        preview = render_tag(
            "div",
            styles={
                "display": "none",
                "overflow": "hidden",
                "line-height": "1px",
                "opacity": "0",
                "max-height": "0",
                "max-width": "0",
            },
            children=[self.preview_text],
            template_mode=template_mode,
        )
        body = render_tag(
            "body",
            styles={
                "margin": "0",
                "padding": "28px 12px 40px",
                "background": theme["body_background"],
                "font-family": theme["font_family"],
                "font-size": theme["base_font_size"],
                "line-height": theme["line_height"],
                "color": theme["text_color"],
            },
            children=[preview, frame],
            template_mode=template_mode,
        )
        head = (
            '<head><meta charset="utf-8"/>'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>'
            f"<title>{render_fragment(self.title, template_mode=template_mode)}</title></head>"
        )
        html_attrs = attrs_to_html({"lang": self.lang}, template_mode=template_mode)
        return f"<!doctype html><html{html_attrs}>{head}{body}</html>"
