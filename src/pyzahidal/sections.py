from __future__ import annotations

from typing import Iterable, Sequence

from .base import (
    ActionSpec,
    AvatarSpec,
    BentoItemSpec,
    BlogPostSpec,
    CartItemSpec,
    FaqItemSpec,
    HeroMediaSpec,
    LogoSpec,
    MenuItemSpec,
    MetricSpec,
    PricingPlanSpec,
    ProductSpec,
    Renderable,
    ReviewSpec,
    SocialLinkSpec,
    TeamMemberSpec,
    TestimonialSpec,
    TimelineStepSpec,
    require_spec,
    require_spec_sequence,
)
from .primitives import (
    Alert,
    Avatar,
    AvatarGroup,
    Button,
    Columns,
    Container,
    DataTable,
    Divider,
    Heading,
    Inline,
    Image,
    Link,
    LogoStrip,
    Menu,
    Metric,
    Pill,
    ProgressBar,
    Row,
    Section,
    Stack,
    Surface,
    SocialLinks,
    Spacer,
    Text,
)
from .rendering import raw, render_tag
from .theme import build_theme


def _theme_kwargs(kwargs: dict[str, object]) -> dict[str, object]:
    return {"theme": kwargs.get("theme"), "theme_overrides": kwargs.get("theme_overrides")}


def _render_button_group(actions: Sequence[ActionSpec] | None, themed: dict[str, object]) -> object:
    if not actions:
        return ""
    buttons = []
    for action in require_spec_sequence(actions, ActionSpec, "actions"):
        buttons.append(
            Button(
                action.label,
                href=action.href,
                variant=action.variant,
                styles={"margin-right": "10px", "margin-bottom": "10px"},
                **themed,
            )
        )
    return raw("".join(button.render() for button in buttons))


def _card_table(children: Sequence[object], theme_map: dict[str, object], padding: str | None = None, *, featured: bool = False) -> str:
    return render_tag(
        "table",
        attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
        styles={
            "width": "100%",
            "border-radius": theme_map["radius_md"],
            "border": f"{'2px' if featured else '1px'} solid {theme_map['card_featured_border_color' if featured else 'card_border_color']}",
            "background": theme_map["card_featured_background" if featured else "card_background"],
        },
        children=[
            raw(
                render_tag(
                    "tr",
                    children=[
                        render_tag(
                            "td",
                            styles={"padding": padding or theme_map["content_padding_compact"]},
                            children=list(children),
                        )
                    ],
                )
            )
        ],
    )


class Header(Container):
    def __init__(
        self,
        brand: str,
        nav_items: Sequence[MenuItemSpec] | None = None,
        *,
        logo_src: str | None = None,
        logo_alt: str = "",
        tagline: str | None = "Purpose-built email components",
        meta_label: str | None = "Email kit",
        **kwargs: object,
    ) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        themed = _theme_kwargs(kwargs)
        meta_children: list[object] = []
        if meta_label:
            meta_children.append(Text(meta_label, size="kicker", tone="muted", align="right", **themed))
        if nav_items:
            meta_children.append(Menu(nav_items, gap="14px", **themed, styles={"text-align": "right"}))
        meta = Stack(
            *meta_children,
            gap="8px",
            align="right",
            **themed,
        )
        brand_children: list[object] = []
        if logo_src:
            brand_children.extend(
                [
                    Image(
                        logo_src,
                        alt=logo_alt or brand,
                        width="auto",
                        block=False,
                        styles={"max-width": "220px", "border-radius": "0"},
                        **themed,
                    ),
                    Spacer("8px"),
                ]
            )
        brand_children.append(Heading(brand, level="small", styles={"font-size": theme_map["subheading_size"]}, **themed))
        if tagline:
            brand_children.extend([Text(tagline, size="small", tone="muted", **themed)])
        brand_block = Stack(*brand_children, gap="6px", **themed)
        content = Section(Columns(brand_block, meta, widths=["52%", "48%"]), padding=theme_map["content_padding_compact"], **themed)
        super().__init__(content, variant="ghost", styles={"box-shadow": "none"}, **kwargs)


class Footer(Container):
    def __init__(
        self,
        company: str,
        social_items: Iterable[SocialLinkSpec] | None = None,
        *,
        top_image_src: str | None = None,
        top_image_alt: str = "",
        description: str | None = "Ship clearer campaigns with reusable blocks and calmer defaults.",
        menu_items: Sequence[MenuItemSpec] | None = None,
        legal_links: Sequence[MenuItemSpec] | None = None,
        disclaimer: str | None = "You are receiving this email because you opted in to product updates.",
        **kwargs: object,
    ) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        themed = _theme_kwargs(kwargs)
        closing_children: list[object] = []
        if top_image_src:
            closing_children.extend([Image(top_image_src, alt=top_image_alt or company, width="100%", **themed), Spacer("14px")])
        closing_children.append(Heading(company, level="small", **themed))
        if description:
            closing_children.append(Text(description, size="small", styles={"color": theme_map["footer_text_color"]}, **themed))
        if menu_items:
            closing_children.append(Menu(menu_items, gap="12px", **themed))
        if social_items:
            closing_children.append(SocialLinks(social_items, **themed))
        closing_children.append(Divider(**themed))
        if legal_links:
            legal = Inline(
                *[Link(item.label, href=item.href, tone="muted", **themed) for item in require_spec_sequence(legal_links, MenuItemSpec, "legal_links")],
                gap="10px",
                wrap=True,
                **themed,
            )
            closing_children.append(legal)
        if disclaimer:
            closing_children.append(Text(disclaimer, size="small", styles={"color": theme_map["footer_text_color"]}, **themed))
        closing = Surface(
            Stack(*closing_children, gap="12px", **themed),
            tone="subtle",
            padding=theme_map["content_padding_compact"],
            radius=theme_map["radius_md"],
            **themed,
        )
        super().__init__(Section(closing, padding="0", **themed), variant="ghost", styles={"box-shadow": "none"}, **kwargs)


class Hero(Container):
    def __init__(
        self,
        *,
        title: str,
        body: str,
        primary_action: ActionSpec,
        eyebrow: str | None = None,
        secondary_action: ActionSpec | None = None,
        media: HeroMediaSpec | None = None,
        meta_items: Sequence[MetricSpec] | None = None,
        **kwargs: object,
    ) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        themed = _theme_kwargs(kwargs)
        left = [
            Pill(
                eyebrow or "New release",
                styles={"background": theme_map["eyebrow_background"], "color": theme_map["eyebrow_text_color"]},
                **themed,
            ),
            Spacer("16px"),
            Heading(title, level="hero", **themed),
            Spacer("14px"),
            Text(body, styles={"color": theme_map["muted_text_color"]}, **themed),
            Spacer("22px"),
            _render_button_group([primary_action, *([secondary_action] if secondary_action else [])], themed),
        ]
        if meta_items:
            normalized_meta_items = require_spec_sequence(meta_items, MetricSpec, "meta_items")
            stat_cells = []
            for item in normalized_meta_items:
                stat_cells.append(
                    render_tag(
                        "td",
                        styles={
                            "padding-right": "14px",
                            "padding-top": "18px",
                            "vertical-align": "top",
                            "width": f"{int(100 / len(normalized_meta_items))}%",
                        },
                        children=[
                            render_tag(
                                "div",
                                styles={"font-size": theme_map["metric_value_size"], "font-weight": "700", "color": theme_map["heading_color"], "font-family": theme_map["heading_font_family"]},
                                children=[item.value],
                            ),
                            render_tag(
                                "div",
                                styles={"font-size": theme_map["body_small_size"], "color": theme_map["muted_text_color"], "font-family": theme_map["font_family"]},
                                children=[item.label],
                            ),
                        ],
                    )
                )
            left.extend(
                [
                    Spacer("18px"),
                    raw(
                        render_tag(
                            "table",
                            attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
                            children=[raw(render_tag("tr", children=[raw(cell) for cell in stat_cells]))],
                        )
                    ),
                ]
            )
        right_markup = ""
        if media:
            media = require_spec(media, HeroMediaSpec, "media")
            right_markup = _card_table(
                [
                    Image(media.src, alt=media.alt or title, framed=True, **themed),
                    Spacer("14px"),
                    Text(media.eyebrow, size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
                    Spacer("4px"),
                    Heading(media.title, level="small", **themed),
                    Spacer("6px"),
                    Text(media.body, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                ],
                theme_map,
                featured=True,
            )
        row_cells = [
            render_tag("td", styles={"width": "58%" if right_markup else "100%", "padding": theme_map["content_padding"], "vertical-align": "top"}, children=left)
        ]
        if right_markup:
            row_cells.append(
                render_tag(
                    "td",
                    styles={
                        "width": "42%",
                        "padding": theme_map["content_padding"],
                        "vertical-align": "top",
                        "background": theme_map["hero_accent_background"],
                        "border-top-right-radius": theme_map["radius_lg"],
                        "border-bottom-right-radius": theme_map["radius_lg"],
                    },
                    children=[raw(right_markup)],
                )
            )
        content = [
            raw(
                render_tag(
                    "table",
                    attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
                    styles={
                        "background": theme_map["hero_background"],
                        "border": f"1px solid {theme_map['hero_border_color']}",
                        "border-radius": theme_map["radius_lg"],
                    },
                    children=[raw(render_tag("tr", children=row_cells))],
                )
            )
        ]
        super().__init__(Section(*content, padding="0", **themed), variant="ghost", styles={"box-shadow": "none"}, **kwargs)


class BentoGrid(Container):
    def __init__(self, items: Sequence[BentoItemSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        cards = []
        for item in require_spec_sequence(items, BentoItemSpec, "items"):
            cards.append(
                raw(
                    _card_table(
                        [
                            Text(item.eyebrow, size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
                            Spacer("8px"),
                            Heading(item.title, level="small", **themed),
                            Spacer("8px"),
                            Text(item.body, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                        ],
                        theme_map,
                    )
                )
            )
            cards.append(Spacer("14px"))
        super().__init__(Section(*(cards[:-1] if cards else []), **themed), **kwargs)


class CallToAction(Container):
    def __init__(self, title: str, body: str, actions: Sequence[ActionSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        content = raw(
            render_tag(
                "div",
                styles={
                    "padding": theme_map["content_padding"],
                    "border-radius": theme_map["radius_lg"],
                    "background": theme_map["alt_surface_color"],
                    "border": f"1px solid {theme_map['border_color']}",
                },
                children=[
                    Text("Call to action", size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
                    Spacer("8px"),
                    Heading(title, level="section", **themed),
                    Spacer("10px"),
                    Text(body, styles={"color": theme_map["muted_text_color"]}, **themed),
                    Spacer("18px"),
                    _render_button_group(actions, themed),
                ],
            )
        )
        super().__init__(Section(content, padding="0", **themed), variant="ghost", styles={"box-shadow": "none"}, **kwargs)


class Feature(Renderable):
    def __init__(
        self,
        title: str,
        body: str,
        icon: str | None = None,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
    ) -> None:
        self.title = title
        self.body = body
        self.icon = icon or "•"
        self.theme = theme
        self.theme_overrides = theme_overrides

    def render(self) -> str:
        return self._render(template_mode=False)

    def render_template(self) -> str:
        return self._render(template_mode=True)

    def _render(self, *, template_mode: bool) -> str:
        theme_map = build_theme(self.theme, self.theme_overrides)
        return _card_table(
            [
                render_tag("div", styles={"font-size": "24px", "line-height": "1"}, children=[self.icon], template_mode=template_mode),
                render_tag("div", styles={"height": "10px"}, template_mode=template_mode),
                Heading(self.title, level="small", theme=self.theme, theme_overrides=self.theme_overrides),
                render_tag("div", styles={"height": "6px"}, template_mode=template_mode),
                Text(
                    self.body,
                    size="small",
                    styles={"color": theme_map["muted_text_color"]},
                    theme=self.theme,
                    theme_overrides=self.theme_overrides,
                ),
            ],
            theme_map,
        )


class Coupon(Container):
    def __init__(self, code: str, detail: str, **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        content = raw(
            render_tag(
                "div",
                styles={
                    "padding": theme_map["content_padding"],
                    "border-radius": theme_map["radius_lg"],
                    "background": theme_map["card_featured_background"],
                    "border": f"2px dashed {theme_map['card_featured_border_color']}",
                },
                children=[
                    Pill("Offer", **themed),
                    Spacer("12px"),
                    Heading(code, level="section", **themed),
                    Spacer("8px"),
                    Text(detail, styles={"color": theme_map["muted_text_color"]}, **themed),
                ],
            )
        )
        super().__init__(Section(content, padding="0", **themed), variant="ghost", styles={"box-shadow": "none"}, **kwargs)


class Stats(Container):
    def __init__(self, items: Sequence[MetricSpec], **kwargs: object) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        normalized_items = require_spec_sequence(items, MetricSpec, "items")
        metrics = [
            Metric(
                item.value,
                label=item.label,
                detail=item.detail,
                trend=item.trend,
                theme=kwargs.get("theme"),
                theme_overrides=kwargs.get("theme_overrides"),
            )
            for item in normalized_items
        ]
        content = Surface(
            Columns(*metrics, widths=[f"{int(100 / len(normalized_items))}%" for _ in normalized_items], gap="10px"),
            tone="default",
            padding=theme_map["card_padding"],
            **_theme_kwargs(kwargs),
        )
        super().__init__(Section(content, padding="0", **_theme_kwargs(kwargs)), **kwargs)


class LogoCloud(Container):
    def __init__(self, logos: Sequence[LogoSpec], **kwargs: object) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        super().__init__(
            LogoStrip(logos, boxed=True, **_theme_kwargs(kwargs)),
            padding=theme_map["content_padding"],
            **kwargs,
        )


class BlogList(Container):
    def __init__(self, posts: Sequence[BlogPostSpec], **kwargs: object) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        themed = _theme_kwargs(kwargs)
        items = []
        for post in require_spec_sequence(posts, BlogPostSpec, "posts"):
            items.extend(
                [
                    raw(
                        _card_table(
                            [
                                Text(post.eyebrow, size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
                                Spacer("8px"),
                                Heading(post.title, level="subsection", **themed),
                                Spacer("8px"),
                                Text(post.excerpt, styles={"color": theme_map["muted_text_color"]}, **themed),
                                Spacer("14px"),
                                Button(post.label, href=post.href, variant="ghost", **themed),
                            ],
                            theme_map,
                        )
                    ),
                    Spacer("14px"),
                ]
            )
        super().__init__(Section(*(items[:-1] if items else []), **themed), **kwargs)


class FAQ(Container):
    def __init__(self, items: Sequence[FaqItemSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        children = []
        for item in require_spec_sequence(items, FaqItemSpec, "items"):
            question = item.question.strip()
            answer = item.answer.strip()
            if not question and not answer:
                continue
            children.extend(
                [
                    raw(
                        _card_table(
                            [
                                Heading(question, level="small", **themed),
                                Spacer("8px"),
                                Text(answer, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                            ],
                            theme_map,
                        )
                    ),
                    Spacer("12px"),
                ]
            )
        super().__init__(Section(*children[:-1] if children else [], **themed), **kwargs)


class Team(Container):
    def __init__(self, members: Sequence[TeamMemberSpec], **kwargs: object) -> None:
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        themed = _theme_kwargs(kwargs)
        cards = []
        for member in require_spec_sequence(members, TeamMemberSpec, "members"):
            image_src = member.image.strip()
            name = member.name.strip()
            role = member.role.strip()
            bio = member.bio.strip()
            meta = member.meta.strip()
            action_label = member.action.label.strip() if member.action else ""
            action_href = member.action.href.strip() if member.action else "#"
            card_children: list[object] = [
                Avatar(image_src, alt=name or "Team member"),
                Spacer("10px"),
                Heading(name or "Team member", level="small", **themed),
            ]
            if role:
                card_children.extend([Spacer("4px"), Text(role, size="small", styles={"color": theme_map["muted_text_color"]}, **themed)])
            if meta:
                card_children.extend([Spacer("4px"), Text(meta, size="small", tone="muted", **themed)])
            if bio:
                card_children.extend([Spacer("8px"), Text(bio, size="small", styles={"color": theme_map["muted_text_color"]}, **themed)])
            if action_label:
                card_children.extend([Spacer("10px"), Button(action_label, href=action_href, variant="ghost", **themed)])
            cards.extend(
                [
                    raw(
                        _card_table(
                            card_children,
                            theme_map,
                        )
                    ),
                    Spacer("12px"),
                ]
            )
        super().__init__(Section(*(cards[:-1] if cards else []), **themed), **kwargs)


class WelcomeHero(Container):
    def __init__(
        self,
        *,
        title: str,
        body: str,
        action: ActionSpec,
        members: Sequence[AvatarSpec] | None = None,
        **kwargs: object,
    ) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        action = require_spec(action, ActionSpec, "action")
        content = Stack(
            Heading(title, level="hero", align="center", styles={"font-size": "34px", "line-height": "1.2"}, **themed),
            AvatarGroup(members or [], size="48px", overlap="12px", align="center"),
            Text(
                body,
                align="center",
                styles={"color": theme_map["muted_text_color"], "font-size": "20px", "line-height": "1.5"},
                **themed,
            ),
            Button(
                action.label,
                href=action.href,
                variant=action.variant,
                styles={"padding": "16px 32px", "font-size": "18px"},
                **themed,
            ),
            gap="26px",
            align="center",
            **themed,
        )
        super().__init__(
            Section(
                Surface(content, tone="ghost", padding="40px 28px 46px", **themed),
                padding="0",
                **themed,
            ),
            variant="ghost",
            styles={"box-shadow": "none"},
            **kwargs,
        )


class Testimonials(Container):
    def __init__(self, items: Sequence[TestimonialSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        blocks = []
        for item in require_spec_sequence(items, TestimonialSpec, "items"):
            blocks.extend(
                [
                    raw(
                        _card_table(
                            [
                                Text(f'"{item.quote}"', styles={"font-style": "italic"}, **themed),
                                Spacer("12px"),
                                Heading(item.author, level="small", **themed),
                                Spacer("4px"),
                                Text(item.role, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                            ],
                            theme_map,
                            featured=True,
                        )
                    ),
                    Spacer("12px"),
                ]
            )
        super().__init__(Section(*blocks[:-1] if blocks else [], **themed), **kwargs)


class Timeline(Container):
    def __init__(self, steps: Sequence[TimelineStepSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        normalized_steps = require_spec_sequence(steps, TimelineStepSpec, "steps")

        rows: list[str] = []
        rail_color = str(theme_map["card_border_color"])
        dot_color = str(theme_map["accent_color"])
        for index, step in enumerate(normalized_steps):
            show_connector = index < len(normalized_steps) - 1
            rows.append(
                render_tag(
                    "tr",
                    children=[
                        render_tag(
                            "td",
                            styles={"width": "136px", "vertical-align": "top", "text-align": "right"},
                            children=[
                                Pill(step.version, **themed),
                                render_tag("div", styles={"height": "8px", "line-height": "8px", "font-size": "8px"}, children=[""]),
                                Heading(step.date, level="small", **themed),
                                render_tag("div", styles={"height": "8px", "line-height": "8px", "font-size": "8px"}, children=[""]),
                                Text(step.category, size="small", styles={"color": theme_map["muted_text_color"], "font-weight": "600"}, **themed),
                            ],
                        ),
                        render_tag("td", styles={"width": "16px"}, children=[""]),
                        render_tag(
                            "td",
                            styles={"width": "14px", "vertical-align": "top"},
                            children=[
                                render_tag(
                                    "div",
                                    styles={
                                        "width": "10px",
                                        "height": "10px",
                                        "border-radius": "999px",
                                        "background": dot_color,
                                        "border": f"2px solid {dot_color}",
                                        "margin": "4px auto 0",
                                    },
                                    children=[""],
                                ),
                                render_tag(
                                    "div",
                                    styles={
                                        "width": "2px",
                                        "height": "72px" if show_connector else "0",
                                        "background": rail_color if show_connector else "transparent",
                                        "margin": "6px auto 0",
                                        "line-height": "0",
                                        "font-size": "0",
                                    },
                                    children=[""],
                                ),
                            ],
                        ),
                        render_tag("td", styles={"width": "16px"}, children=[""]),
                        render_tag(
                            "td",
                            styles={"vertical-align": "top"},
                            children=[
                                Surface(
                                    Stack(
                                        Heading(step.title, level="small", **themed),
                                        Text(step.detail, styles={"color": theme_map["muted_text_color"]}, **themed),
                                        gap="12px",
                                        **themed,
                                    ),
                                    tone="subtle",
                                    padding="18px",
                                    radius=theme_map["radius_md"],
                                    **themed,
                                )
                            ],
                        ),
                    ],
                )
            )
            if show_connector:
                rows.append(
                    render_tag(
                        "tr",
                        children=[render_tag("td", attrs={"colspan": "5"}, styles={"height": "14px", "line-height": "14px", "font-size": "14px"}, children=[""])],
                    )
                )
        timeline = raw(
            render_tag(
                "table",
                attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
                styles={"width": "100%"},
                children=[raw("".join(rows))],
            )
        )
        super().__init__(Section(timeline, **themed), **kwargs)


class Pricing(Container):
    def __init__(self, plans: Sequence[PricingPlanSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        content = []
        for plan in require_spec_sequence(plans, PricingPlanSpec, "plans"):
            action = plan.action
            features = plan.features
            feature_markup = []
            for feature in features:
                feature_markup.extend(
                    [
                        Text(f"• {feature}", size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                        Spacer("6px"),
                    ]
                )
            card_children = []
            if plan.badge:
                card_children.extend([Pill(plan.badge, **themed), Spacer("12px")])
            card_children.extend(
                [
                    Heading(plan.name, level="subsection", **themed),
                    Spacer("6px"),
                    Text(plan.price, styles={"font-size": theme_map["subheading_size"], "font-weight": "700", "color": theme_map["heading_color"]}, **themed),
                    Spacer("6px"),
                    Text(plan.description, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                ]
            )
            if feature_markup:
                card_children.extend([Spacer("14px"), *feature_markup[:-1]])
            card_children.extend([Spacer("16px"), Button(action.label, href=action.href, variant=action.variant, **themed)])
            content.extend(
                [
                    raw(_card_table(card_children, theme_map, featured=plan.featured)),
                    Spacer("14px"),
                ]
            )
        super().__init__(Section(*content[:-1] if content else [], **themed), **kwargs)


class ProductList(Container):
    def __init__(self, products: Sequence[ProductSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        items = []
        for product in require_spec_sequence(products, ProductSpec, "products"):
            product_content = []
            image_src = product.image_src.strip()
            name = product.name.strip() or "Product"
            price = product.price.strip()
            description = product.description.strip()
            rating = product.rating.strip()
            reviews = product.reviews.strip()
            badge = product.badge.strip()
            action = product.action or ActionSpec(product.label, href=product.href, variant="secondary")
            action_label = action.label.strip()
            action_href = action.href.strip()
            action_variant = action.variant.strip()
            if image_src:
                product_content.extend([Image(image_src, alt=name, framed=True, **themed), Spacer("12px")])
            if badge:
                product_content.extend([Pill(badge, **themed), Spacer("8px")])
            product_content.extend(
                [
                    Heading(name, level="small", **themed),
                    Spacer("6px"),
                ]
            )
            if price:
                product_content.extend([Text(price, styles={"font-weight": "700", "color": theme_map["heading_color"]}, **themed), Spacer("6px")])
            if description:
                product_content.extend([Text(description, size="small", styles={"color": theme_map["muted_text_color"]}, **themed), Spacer("8px")])
            if rating or reviews:
                rating_line = " ".join(part for part in (rating, reviews) if part).strip()
                product_content.extend([Text(rating_line, size="small", tone="muted", **themed), Spacer("12px")])
            else:
                product_content.extend([Spacer("12px")])
            product_content.append(Button(action_label, href=action_href, variant=action_variant, **themed))
            items.extend([raw(_card_table(product_content, theme_map)), Spacer("14px")])
        super().__init__(Section(*items[:-1] if items else [], **themed), **kwargs)


class ProductDetail(Container):
    def __init__(
        self,
        name: str,
        price: str,
        description: str,
        image_src: str = "",
        *,
        action: ActionSpec | None = None,
        href: str = "#",
        label: str = "Shop now",
        variant: str = "primary",
        **kwargs: object,
    ) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        media = Image(image_src, alt=name, framed=True, **themed) if image_src else ""
        resolved_action = require_spec(action, ActionSpec, "action") if action is not None else ActionSpec(label, href=href, variant=variant)
        copy = raw(
            _card_table(
                [
                    Text("Featured product", size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
                    Spacer("8px"),
                    Heading(name, level="section", **themed),
                    Spacer("8px"),
                    Text(price, styles={"font-size": theme_map["subheading_size"], "font-weight": "700", "color": theme_map["heading_color"]}, **themed),
                    Spacer("8px"),
                    Text(description, styles={"color": theme_map["muted_text_color"]}, **themed),
                    Spacer("16px"),
                    Button(resolved_action.label, href=resolved_action.href, variant=resolved_action.variant, **themed),
                ],
                theme_map,
                featured=True,
            )
        )
        section_children = [copy]
        if image_src:
            section_children = [Row(media, copy, gap="18px")]
        super().__init__(Section(*section_children, **themed), **kwargs)


class ProductFeatures(Container):
    def __init__(self, features: Sequence[str], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        items = []
        for feature in features:
            items.extend(
                [
                    Alert(Text(feature, size="small", **themed), styles={"background": theme_map["muted_surface_color"]}, **themed),
                    Spacer("8px"),
                ]
            )
        super().__init__(Section(*items[:-1] if items else [], **themed), **kwargs)


class CategoryPreview(Container):
    def __init__(self, title: str, categories: Sequence[tuple[str, str]], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        items = [Heading(title, level="subsection", **themed), Spacer("10px")]
        for label, href in categories:
            items.extend([Button(label, href=href, variant="secondary", styles={"margin-right": "8px", "margin-bottom": "8px"}, **themed)])
        super().__init__(Section(*items, **themed), **kwargs)


class ShoppingCart(Container):
    def __init__(self, items: Sequence[CartItemSpec], **kwargs: object) -> None:
        rows = [(item.name, item.qty, item.price) for item in require_spec_sequence(items, CartItemSpec, "items")]
        themed = _theme_kwargs(kwargs)
        super().__init__(Section(DataTable(headers=["Item", "Qty", "Price"], rows=rows, **themed), **themed), **kwargs)


class Reviews(Container):
    def __init__(self, items: Sequence[ReviewSpec], **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        cards: list[object] = []
        for item in require_spec_sequence(items, ReviewSpec, "items"):
            quote = item.quote.strip()
            author = item.author.strip()
            role = item.role.strip()
            rating = item.rating.strip()
            image_src = item.src.strip()
            action_label = item.action.label.strip() if item.action else ""
            action_href = item.action.href.strip() if item.action else "#"
            card_children: list[object] = []
            if rating:
                card_children.extend([Text(rating, size="small", tone="muted", **themed), Spacer("8px")])
            if quote:
                card_children.extend([Text(f'"{quote}"', styles={"font-style": "italic"}, **themed), Spacer("12px")])
            author_row: list[object] = []
            if image_src:
                author_row.append(Avatar(image_src, alt=author, size="40px"))
            author_stack = Stack(
                Heading(author, level="small", **themed),
                Text(role, size="small", styles={"color": theme_map["muted_text_color"]}, **themed),
                gap="4px",
                **themed,
            )
            if author_row:
                author_row.append(author_stack)
                card_children.append(Inline(*author_row, gap="10px", **themed))
            else:
                card_children.append(author_stack)
            if action_label:
                card_children.extend([Spacer("10px"), Button(action_label, href=action_href, variant="ghost", **themed)])
            cards.extend(
                [
                    raw(_card_table(card_children, theme_map, featured=True)),
                    Spacer("12px"),
                ]
            )
        super().__init__(Section(*(cards[:-1] if cards else []), **themed), **kwargs)


class OrderSummary(Container):
    def __init__(self, rows: Sequence[tuple[str, str]], progress: int | None = None, **kwargs: object) -> None:
        themed = _theme_kwargs(kwargs)
        theme_map = build_theme(kwargs.get("theme"), kwargs.get("theme_overrides"))
        content: list[object] = [
            Text("Order summary", size="kicker", styles={"color": theme_map["muted_text_color"]}, **themed),
            Spacer("8px"),
            DataTable(headers=["Label", "Value"], rows=rows, **themed),
        ]
        if progress is not None:
            content.extend([Spacer("14px"), Text("Fulfillment progress", size="small", styles={"color": theme_map["muted_text_color"]}, **themed), Spacer("8px"), ProgressBar(progress, **themed)])
        super().__init__(Section(*content, **themed), **kwargs)
