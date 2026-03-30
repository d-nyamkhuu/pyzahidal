from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

from .base import (
    AvatarSpec,
    Component,
    DataColumnSpec,
    DeferredComponent,
    ImageSpec,
    LogoSpec,
    MenuItemSpec,
    SocialLinkSpec,
    require_spec_sequence,
)
from .rendering import raw, render_tag
from .theme import build_theme


def _resolve_gap(theme_map: Mapping[str, object], gap: str | None, fallback: str = "gap_md") -> str:
    if gap is None:
        return str(theme_map.get(fallback, "16px"))
    return str(theme_map.get(gap, gap))


def _normalize_items(items: Iterable[object]) -> list[object]:
    return [item for item in items if item not in (None, "")]


def _coerce_tabular_rows(rows: object) -> list[Sequence[object] | Mapping[str, object]]:
    if rows is None:
        return []
    if not isinstance(rows, (list, tuple)) and hasattr(rows, "to_dict") and callable(rows.to_dict):
        to_dict = rows.to_dict
        try:
            rows = to_dict(orient="records")
        except TypeError:
            rows = to_dict("records")
    if isinstance(rows, Mapping):
        raise ValueError("rows must be a sequence of rows, not a mapping")
    return list(rows)


def _resolved_theme(theme_overrides: dict[str, object] | None) -> dict[str, object]:
    return build_theme(None, theme_overrides)


def _deferred_kwargs(kwargs: dict[str, object], theme_overrides: dict[str, object] | None) -> dict[str, object]:
    deferred = dict(kwargs)
    deferred.pop("theme", None)
    deferred.pop("theme_overrides", None)
    return deferred


class Surface(DeferredComponent):
    tag = "table"
    default_styles = {"width": "100%"}

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        tone: str = "default",
        padding: str | None = None,
        radius: str | None = None,
        border: str | None = None,
        shadow: str | None = None,
        background_image: str | None = None,
        background_size: str = "cover",
        background_position: str = "center",
        background_color: str | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Surface(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                tone=tone,
                padding=padding,
                radius=radius,
                border=border,
                shadow=shadow,
                background_image=background_image,
                background_size=background_size,
                background_position=background_position,
                background_color=background_color,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        kwargs.setdefault("attrs", {"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"})
        styles = kwargs.pop("styles", {})
        tone_styles = {
            "default": {
                "background": theme_map["surface_default_background"],
                "border": f"1px solid {theme_map['surface_default_border_color']}",
                "box-shadow": theme_map["surface_default_shadow"],
            },
            "subtle": {
                "background": theme_map["surface_subtle_background"],
                "border": f"1px solid {theme_map['surface_subtle_border_color']}",
                "box-shadow": theme_map["surface_subtle_shadow"],
            },
            "featured": {
                "background": theme_map["surface_featured_background"],
                "border": f"2px solid {theme_map['surface_featured_border_color']}",
                "box-shadow": theme_map["surface_featured_shadow"],
            },
            "inverse": {
                "background": theme_map["surface_inverse_background"],
                "border": f"1px solid {theme_map['surface_inverse_border_color']}",
                "box-shadow": theme_map["surface_inverse_shadow"],
            },
            "overlay": {
                "background": theme_map["background_overlay_color"],
                "border": "1px solid rgba(255, 255, 255, 0.12)",
                "box-shadow": "none",
            },
            "ghost": {
                "background": "transparent",
                "border": "0",
                "box-shadow": "none",
            },
        }
        merged_styles = {
            "width": "100%",
            "border-radius": radius or theme_map["radius_card"],
            **tone_styles.get(tone, tone_styles["default"]),
        }
        if border is not None:
            merged_styles["border"] = border
        if shadow is not None:
            merged_styles["box-shadow"] = shadow
        if background_color is not None:
            merged_styles["background"] = background_color
        if background_image:
            merged_styles["background-image"] = f"url('{background_image}')"
            merged_styles["background-size"] = background_size
            merged_styles["background-position"] = background_position
        merged_styles.update(styles)
        cell = render_tag(
            "tr",
            children=[
                render_tag(
                    "td",
                    styles={"padding": padding or "0"},
                    children=list(children),
                )
            ],
        )
        super().__init__(raw(cell), styles=merged_styles, **kwargs)


class Container(Surface):
    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        variant: str = "default",
        **kwargs: object,
    ) -> None:
        super().__init__(*children, theme=theme, theme_overrides=theme_overrides, tone=variant, **kwargs)


class Section(DeferredComponent):
    tag = "table"

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        padding: str | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Section(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                padding=padding,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        kwargs.setdefault("attrs", {"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"})
        styles = kwargs.pop("styles", {})
        merged_styles = {"width": "100%"}
        merged_styles.update(styles)
        cell = render_tag(
            "tr",
            children=[
                render_tag(
                    "td",
                    styles={"padding": padding or theme_map["section_padding"]},
                    children=list(children),
                )
            ],
        )
        super().__init__(raw(cell), styles=merged_styles, **kwargs)


class Stack(DeferredComponent):
    tag = "table"

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        gap: str | None = None,
        divider: bool = False,
        align: str = "left",
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Stack(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                gap=gap,
                divider=divider,
                align=align,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        kwargs.setdefault("attrs", {"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"})
        items = _normalize_items(children)
        rows: list[str] = []
        row_gap = _resolve_gap(theme_map, gap)
        for index, child in enumerate(items):
            rows.append(
                render_tag(
                    "tr",
                    children=[
                        render_tag(
                            "td",
                            styles={"text-align": align},
                            children=[child],
                        )
                    ],
                )
            )
            if index < len(items) - 1:
                if divider:
                    rows.append(
                        render_tag(
                            "tr",
                            children=[
                                render_tag(
                                    "td",
                                    styles={"padding": f"{row_gap} 0"},
                                    children=[Divider(theme=theme, theme_overrides=theme_overrides)],
                                )
                            ],
                        )
                    )
                else:
                    rows.append(render_tag("tr", children=[render_tag("td", styles={"height": row_gap, "line-height": row_gap, "font-size": row_gap}, children=[""])]))
        super().__init__(raw("".join(rows)), **kwargs)


class Inline(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        gap: str | None = None,
        align: str = "left",
        wrap: bool = False,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Inline(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                gap=gap,
                align=align,
                wrap=wrap,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        item_gap = _resolve_gap(theme_map, gap, "gap_sm")
        normalized_children = _normalize_items(children)
        items = []
        for index, child in enumerate(normalized_children):
            child_styles = {
                "display": "inline-block",
                "vertical-align": "top",
            }
            if index < len(normalized_children) - 1:
                child_styles["margin-right"] = item_gap
            if wrap:
                child_styles["margin-bottom"] = item_gap
            items.append(render_tag("span", styles=child_styles, children=[child]))
        merged_styles = {"text-align": align}
        merged_styles.update(styles)
        super().__init__(*[raw(item) for item in items], styles=merged_styles, **kwargs)


class Columns(Component):
    tag = "table"

    def __init__(
        self,
        *columns: object,
        widths: Sequence[str] | None = None,
        gap: str = "16px",
        stack_on_mobile: bool = False,
        vertical_align: str = "top",
        **kwargs: object,
    ) -> None:
        attrs = dict(kwargs.pop("attrs", {}) or {})
        attrs.setdefault("role", "presentation")
        attrs.setdefault("cellpadding", "0")
        attrs.setdefault("cellspacing", "0")
        attrs.setdefault("width", "100%")
        cells = []
        total = len(columns)
        normalized_widths = list(widths or [])
        for index, column in enumerate(columns):
            width = normalized_widths[index] if index < len(normalized_widths) else f"{int(100 / total)}%" if total else "100%"
            cell_styles = {"vertical-align": vertical_align, "width": width}
            if index < total - 1:
                cell_styles["padding-right"] = gap
            cells.append(render_tag("td", styles=cell_styles, children=[column]))
        self._stack_on_mobile = stack_on_mobile
        self._stack_gap = gap
        self._stack_class = ""
        if stack_on_mobile:
            safe_gap = re.sub(r"[^a-zA-Z0-9_-]+", "-", gap).strip("-") or "gap"
            self._stack_class = f"pz-stack-mobile-{total or 1}-{safe_gap}"
            attrs["class"] = f'{attrs.get("class", "").strip()} {self._stack_class}'.strip()
        super().__init__(raw(render_tag("tr", children=[raw(cell) for cell in cells])), attrs=attrs, **kwargs)

    def _mobile_stack_prefix(self) -> str:
        if not self._stack_on_mobile:
            return ""
        gap = self._stack_gap
        class_name = self._stack_class
        return (
            "<style>"
            "@media only screen and (max-width: 600px) {"
            f".{class_name}, .{class_name} tbody, .{class_name} tr, .{class_name} td {{display:block !important; width:100% !important;}}"
            f".{class_name} td {{padding-right:0 !important; padding-bottom:{gap} !important;}}"
            f".{class_name} td:last-child {{padding-bottom:0 !important;}}"
            "}"
            "</style>"
        )

    def render(self) -> str:
        return f"{self._mobile_stack_prefix()}{super().render()}"

    def render_template(self) -> str:
        return f"{self._mobile_stack_prefix()}{super().render_template()}"


class Row(Columns):
    def __init__(self, *columns: object, gap: str = "16px", stack_on_mobile: bool = False, vertical_align: str = "top", **kwargs: object) -> None:
        super().__init__(*columns, gap=gap, stack_on_mobile=stack_on_mobile, vertical_align=vertical_align, **kwargs)


class Column(Component):
    tag = "div"

    def __init__(self, *children: object, width: str = "50%", **kwargs: object) -> None:
        styles = kwargs.pop("styles", {})
        merged_styles = {"display": "inline-block", "width": width, "vertical-align": "top"}
        merged_styles.update(styles)
        super().__init__(*children, styles=merged_styles, **kwargs)


class Spacer(Component):
    tag = "div"

    def __init__(self, size: str = "16px", **kwargs: object) -> None:
        super().__init__("", styles={"height": size, "line-height": size, "font-size": size}, **kwargs)


class Divider(DeferredComponent):
    tag = "hr"

    def __init__(
        self,
        color: str | None = None,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Divider(
                color=color,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        merged_styles = {"border": "0", "border-top": f"1px solid {color or theme_map['divider_color']}", "margin": "0"}
        merged_styles.update(styles)
        super().__init__(styles=merged_styles, **kwargs)


class Text(DeferredComponent):
    tag = "p"

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        size: str = "body",
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Text(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                size=size,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        align = kwargs.pop("align", None)
        tone = kwargs.pop("tone", "default")
        size_styles = {
            "body": {"font-size": theme_map["base_font_size"]},
            "small": {"font-size": theme_map["body_small_size"]},
            "kicker": {"font-size": theme_map["kicker_size"], "letter-spacing": "0.08em", "text-transform": "uppercase"},
        }
        tone_colors = {
            "default": theme_map["text_color"],
            "muted": theme_map["muted_text_color"],
            "inverse": theme_map["background_overlay_text_color"],
            "accent": theme_map["accent_color"],
        }
        merged_styles = {
            "margin": "0",
            "color": tone_colors.get(tone, theme_map["text_color"]),
            "font-family": theme_map["font_family"],
            "line-height": theme_map["line_height"],
            **size_styles.get(size, size_styles["body"]),
        }
        if align:
            merged_styles["text-align"] = align
        merged_styles.update(styles)
        super().__init__(*children, styles=merged_styles, **kwargs)


class Heading(DeferredComponent):
    tag = "h2"

    def __init__(
        self,
        *children: object,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        level: str = "section",
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Heading(
                *children,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                level=level,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        align = kwargs.pop("align", None)
        tone = kwargs.pop("tone", "default")
        level_styles = {
            "hero": {"font-size": theme_map["hero_title_size"], "line-height": "1.08"},
            "section": {"font-size": theme_map["heading_size"], "line-height": "1.15"},
            "subsection": {"font-size": theme_map["subheading_size"], "line-height": "1.2"},
            "small": {"font-size": theme_map["title_small_size"], "line-height": "1.25"},
        }
        merged_styles = {
            "margin": "0",
            "color": theme_map["background_overlay_text_color"] if tone == "inverse" else theme_map["heading_color"],
            "font-family": theme_map["heading_font_family"],
            **level_styles.get(level, level_styles["section"]),
        }
        if align:
            merged_styles["text-align"] = align
        merged_styles.update(styles)
        super().__init__(*children, styles=merged_styles, **kwargs)


class Image(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        src: str,
        alt: str = "",
        width: str = "100%",
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        framed: bool = False,
        href: str | None = None,
        caption: object | None = None,
        block: bool = True,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Image(
                src,
                alt=alt,
                width=width,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                framed=framed,
                href=href,
                caption=caption,
                block=block,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        merged_styles = {
            "display": "block" if block else "inline-block",
            "width": width,
            "max-width": "100%",
            "border-radius": theme_map["image_radius"],
            "background": theme_map["image_frame_background"] if framed else None,
            "border": f"1px solid {theme_map['card_border_color']}" if framed else None,
        }
        merged_styles.update(styles)
        image_tag = render_tag("img", attrs={"src": src, "alt": alt}, styles=merged_styles)
        content: object = raw(image_tag)
        if href:
            content = raw(render_tag("a", attrs={"href": href}, children=[raw(image_tag)]))
        if caption is not None:
            content = raw(
                render_tag(
                    "div",
                    children=[
                        content,
                        render_tag("div", styles={"height": theme_map["gap_sm"], "line-height": theme_map["gap_sm"], "font-size": theme_map["gap_sm"]}, children=[""]),
                        caption,
                    ],
                )
            )
            super().__init__(content, **kwargs)
            return
        super().__init__(content, **kwargs)


class Button(DeferredComponent):
    tag = "a"

    def __init__(
        self,
        label: str,
        href: str = "#",
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        variant: str = "primary",
        icon_src: str | None = None,
        icon_alt: str = "",
        icon_side: str = "right",
        align: str | None = None,
        radius: str | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Button(
                label,
                href=href,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                variant=variant,
                icon_src=icon_src,
                icon_alt=icon_alt,
                icon_side=icon_side,
                align=align,
                radius=radius,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        variant_styles = {
            "primary": {
                "background": theme_map["primary_color"],
                "color": theme_map["primary_text_color"],
                "border": f"1px solid {theme_map['primary_color']}",
            },
            "secondary": {
                "background": theme_map["button_secondary_background"],
                "color": theme_map["button_secondary_text_color"],
                "border": f"1px solid {theme_map['button_secondary_background']}",
            },
            "ghost": {
                "background": "transparent",
                "color": theme_map["button_ghost_text_color"],
                "border": f"1px solid {theme_map['border_color']}",
            },
        }
        merged_styles = {
            "display": "inline-block",
            "padding": theme_map["button_padding"],
            "text-decoration": "none",
            "border-radius": radius or theme_map["button_radius"],
            "font-weight": "700",
            "font-family": theme_map["font_family"],
            "font-size": theme_map["body_small_size"],
            "text-align": align,
            **variant_styles.get(variant, variant_styles["primary"]),
        }
        merged_styles.update(styles)
        children: list[object] = [label]
        if icon_src:
            icon = render_tag(
                "img",
                attrs={"src": icon_src, "alt": icon_alt},
                styles={"width": "12px", "height": "12px", "vertical-align": "middle", "margin-left": "8px" if icon_side == "right" else None, "margin-right": "8px" if icon_side == "left" else None},
            )
            children = [raw(icon), label] if icon_side == "left" else [label, raw(icon)]
        super().__init__(*children, attrs={"href": href}, styles=merged_styles, **kwargs)


class Link(DeferredComponent):
    tag = "a"

    def __init__(
        self,
        label: object,
        href: str = "#",
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        tone: str = "default",
        underline: bool = False,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Link(
                label,
                href=href,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                tone=tone,
                underline=underline,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        colors = {
            "default": theme_map["link_color"],
            "muted": theme_map["menu_link_color"],
            "inverse": theme_map["background_overlay_link_color"],
        }
        merged_styles = {
            "color": colors.get(tone, theme_map["link_color"]),
            "text-decoration": "underline" if underline else "none",
            "font-family": theme_map["font_family"],
            "font-size": theme_map["body_small_size"],
        }
        merged_styles.update(styles)
        super().__init__(label, attrs={"href": href}, styles=merged_styles, **kwargs)


class Pill(DeferredComponent):
    tag = "span"

    def __init__(
        self,
        label: str,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        tone: str = "default",
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Pill(
                label,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                tone=tone,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        palettes = {
            "default": (theme_map["pill_background"], theme_map["pill_text_color"]),
            "success": (theme_map["pill_success_background"], theme_map["pill_success_text_color"]),
            "warning": (theme_map["pill_warning_background"], theme_map["pill_warning_text_color"]),
            "danger": (theme_map["pill_danger_background"], theme_map["pill_danger_text_color"]),
        }
        background, color = palettes.get(tone, palettes["default"])
        merged_styles = {
            "display": "inline-block",
            "padding": "7px 12px",
            "background": background,
            "color": color,
            "border-radius": theme_map["radius_pill"],
            "font-size": theme_map["kicker_size"],
            "font-weight": "700",
            "letter-spacing": "0.04em",
            "font-family": theme_map["font_family"],
            "text-transform": "uppercase",
        }
        merged_styles.update(styles)
        super().__init__(label, styles=merged_styles, **kwargs)


class Avatar(Component):
    tag = "img"

    def __init__(self, src: str, alt: str = "", size: str = "56px", **kwargs: object) -> None:
        styles = kwargs.pop("styles", {})
        merged_styles = {
            "width": size,
            "height": size,
            "border-radius": "999px",
            "display": "inline-block",
            "border": "2px solid rgba(255,255,255,0.8)",
        }
        merged_styles.update(styles)
        super().__init__(attrs={"src": src, "alt": alt}, styles=merged_styles, **kwargs)


class AvatarGroup(Component):
    tag = "div"

    def __init__(
        self,
        items: Sequence[AvatarSpec],
        *,
        size: str = "48px",
        overlap: str = "14px",
        align: str = "center",
        **kwargs: object,
    ) -> None:
        styles = kwargs.pop("styles", {})
        children = []
        for index, item in enumerate(require_spec_sequence(items, AvatarSpec, "items")):
            wrapper_styles = {"display": "inline-block", "vertical-align": "middle"}
            if index > 0:
                wrapper_styles["margin-left"] = f"-{overlap}"
            children.append(
                render_tag(
                    "span",
                    styles=wrapper_styles,
                    children=[
                        Avatar(
                            item.src,
                            alt=item.alt,
                            size=size,
                            styles={"border": "3px solid #ffffff"},
                        )
                    ],
                )
            )
        merged_styles = {"text-align": align}
        merged_styles.update(styles)
        super().__init__(*[raw(child) for child in children], styles=merged_styles, **kwargs)


class Alert(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        *children: object,
        tone: str = "info",
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Alert(
                *children,
                tone=tone,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        palette = {
            "info": theme_map["alert_info_background"],
            "success": theme_map["alert_success_background"],
            "warning": theme_map["alert_warning_background"],
            "danger": theme_map["alert_danger_background"],
        }
        styles = kwargs.pop("styles", {})
        merged_styles = {
            "padding": "14px 16px",
            "background": palette.get(tone, palette["info"]),
            "border": f"1px solid {theme_map['border_color']}",
            "border-radius": theme_map["radius_md"],
        }
        merged_styles.update(styles)
        super().__init__(*children, styles=merged_styles, **kwargs)


class Nav(Component):
    tag = "div"


class Menu(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        items: Iterable[MenuItemSpec],
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        orientation: str = "horizontal",
        gap: str = "14px",
        **kwargs: object,
    ) -> None:
        if theme is None:
            deferred_items = list(items)
            self._deferred_factory = lambda: Menu(
                deferred_items,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                orientation=orientation,
                gap=gap,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        themed = {"theme": theme, "theme_overrides": theme_overrides}
        links = []
        for item in require_spec_sequence(list(items), MenuItemSpec, "items"):
            links.append(Link(item.label, href=item.href, tone="muted", **themed))
        if orientation == "vertical":
            markup = Stack(*links, theme=theme, theme_overrides=theme_overrides, gap=gap)
        else:
            markup = Inline(*links, theme=theme, theme_overrides=theme_overrides, gap=gap)
        super().__init__(markup, **kwargs)


class IconLink(DeferredComponent):
    tag = "a"

    def __init__(
        self,
        href: str,
        icon_src: str,
        alt: str = "",
        label: object | None = None,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        shape: str = "circle",
        size: str = "40px",
        background: str | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: IconLink(
                href,
                icon_src,
                alt=alt,
                label=label,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                shape=shape,
                size=size,
                background=background,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        styles = kwargs.pop("styles", {})
        radius = theme_map["radius_pill"] if shape == "circle" else theme_map["radius_sm"]
        merged_styles = {
            "display": "inline-block",
            "width": size,
            "height": size,
            "line-height": "1",
            "text-align": "center",
            "background": background or theme_map["social_tile_background"],
            "border": f"1px solid {theme_map['social_tile_border_color']}",
            "border-radius": radius,
            "text-decoration": "none",
            "vertical-align": "middle",
        }
        merged_styles.update(styles)
        icon = render_tag("img", attrs={"src": icon_src, "alt": alt}, styles={"width": "20px", "height": "20px", "display": "block", "margin": "0 auto"})
        if label is None:
            icon_markup = render_tag(
                "table",
                attrs={"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"},
                styles={"width": "100%", "height": size},
                children=[
                    raw(
                        render_tag(
                            "tr",
                            children=[
                                render_tag(
                                    "td",
                                    attrs={"align": "center", "valign": "middle"},
                                    styles={"text-align": "center", "vertical-align": "middle", "height": size},
                                    children=[raw(icon)],
                                )
                            ],
                        )
                    )
                ],
            )
            children: list[object] = [raw(icon_markup)]
        else:
            children = [
                raw(icon),
                raw(render_tag("span", styles={"display": "inline-block", "width": theme_map["gap_xs"]}, children=[""])),
                label,
            ]
        super().__init__(*children, attrs={"href": href}, styles=merged_styles, **kwargs)


class ProgressBar(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        value: int,
        max_value: int = 100,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: ProgressBar(
                value,
                max_value=max_value,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        percent = 0 if max_value <= 0 else max(0, min(100, int(value / max_value * 100)))
        track = render_tag(
            "div",
            styles={
                "background": theme_map["border_color"],
                "border-radius": "999px",
                "height": "10px",
                "overflow": "hidden",
            },
            children=[
                raw(
                    render_tag(
                        "div",
                        styles={
                            "background": theme_map["primary_color"],
                            "width": f"{percent}%",
                            "height": "10px",
                            "border-radius": "999px",
                        },
                    )
                )
            ],
        )
        super().__init__(raw(track), **kwargs)


class DataTable(DeferredComponent):
    tag = "table"

    def __init__(
        self,
        headers: Sequence[str] | None = None,
        rows: object = (),
        *,
        columns: Sequence[DataColumnSpec] | None = None,
        compact: bool = False,
        striped: bool = False,
        frame: bool = True,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: DataTable(
                headers=headers,
                rows=rows,
                columns=columns,
                compact=compact,
                striped=striped,
                frame=frame,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        kwargs.setdefault("attrs", {"role": "presentation", "cellpadding": "0", "cellspacing": "0", "width": "100%"})
        styles = kwargs.pop("styles", {})
        normalized_rows = _coerce_tabular_rows(rows)
        uses_mapping_rows = any(isinstance(row, Mapping) for row in normalized_rows)
        if columns is None:
            if not headers:
                raise ValueError("DataTable requires non-empty headers or columns")
            if uses_mapping_rows:
                columns = [DataColumnSpec(key=str(header), header=header) for header in headers]
            else:
                columns = [DataColumnSpec(key=str(index), header=header) for index, header in enumerate(headers)]
        normalized_columns = require_spec_sequence(list(columns), DataColumnSpec, "columns")
        if not normalized_columns:
            raise ValueError("DataTable requires at least one column")
        column_keys = [column.key for column in normalized_columns]
        if len(set(column_keys)) != len(column_keys):
            raise ValueError("DataTable column keys must be unique")
        header_padding = "8px 10px" if compact else str(theme_map["table_header_padding"])
        cell_padding = "8px 10px" if compact else str(theme_map["table_cell_padding"])
        header_cells = [
            render_tag(
                "th",
                styles={
                    "text-align": "left",
                    "padding": header_padding,
                    "width": column.width or None,
                    "border-bottom": f"1px solid {theme_map['table_header_border_color']}",
                    "color": theme_map["heading_color"],
                    "font-family": theme_map["heading_font_family"],
                    "font-size": theme_map["body_small_size"],
                },
                children=[column.header],
            )
            for column in normalized_columns
        ]
        body_rows = []
        for row_index, row in enumerate(normalized_rows):
            if isinstance(row, Mapping):
                cells = [row.get(column.key, "") for column in normalized_columns]
            else:
                if isinstance(row, (str, bytes)):
                    raise ValueError("DataTable row values must be sequences or mappings, not strings")
                cells = list(row)
                if len(cells) != len(normalized_columns):
                    raise ValueError(
                        f"DataTable row {row_index + 1} has {len(cells)} cells but expected {len(normalized_columns)}"
                    )
            body_rows.append(
                render_tag(
                    "tr",
                    children=[
                        render_tag(
                            "td",
                            styles={
                                "padding": cell_padding,
                                "border-bottom": f"1px solid {theme_map['table_row_border_color']}",
                                "text-align": column.align,
                                "color": theme_map["text_color"],
                                "font-family": theme_map["font_family"],
                                "background": theme_map["muted_surface_color"] if striped and row_index % 2 else theme_map["surface_color"],
                            },
                            children=[cell],
                        )
                        for column, cell in zip(normalized_columns, cells)
                    ],
                )
            )
        merged_styles = {
            "border-collapse": "separate",
            "border-spacing": "0",
            "border": f"1px solid {theme_map['card_border_color']}" if frame else "0",
            "border-radius": theme_map["table_radius"],
            "overflow": "hidden",
            "background": theme_map["surface_color"],
        }
        if not frame:
            merged_styles["border-radius"] = "0"
        merged_styles.update(styles)
        super().__init__(
            raw(render_tag("thead", children=[raw(render_tag("tr", children=[raw(cell) for cell in header_cells]))])),
            raw(render_tag("tbody", children=[raw(row) for row in body_rows])),
            styles=merged_styles,
            **kwargs,
        )


class SocialLinks(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        items: Iterable[SocialLinkSpec],
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        mode: str = "text",
        **kwargs: object,
    ) -> None:
        if theme is None:
            deferred_items = list(items)
            self._deferred_factory = lambda: SocialLinks(
                deferred_items,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                mode=mode,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        children: list[object] = []
        for item in require_spec_sequence(list(items), SocialLinkSpec, "items"):
            if mode == "icon" or item.icon_src:
                children.append(
                    IconLink(
                        href=item.href,
                        icon_src=item.icon_src,
                        alt=item.alt or item.label,
                        theme=theme,
                        theme_overrides=theme_overrides,
                    )
                )
            else:
                children.append(Link(item.label, href=item.href, theme=theme, theme_overrides=theme_overrides))
        super().__init__(Inline(*children, theme=theme, theme_overrides=theme_overrides, gap=theme_map["gap_sm"], wrap=True), **kwargs)


class Metric(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        value: object,
        label: object | None = None,
        detail: object | None = None,
        trend: str | None = None,
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            self._deferred_factory = lambda: Metric(
                value,
                label=label,
                detail=detail,
                trend=trend,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        children: list[object] = [
            render_tag(
                "div",
                styles={"font-size": theme_map["metric_value_size"], "font-weight": "700", "color": theme_map["heading_color"], "font-family": theme_map["heading_font_family"]},
                children=[value],
            )
        ]
        if label is not None:
            children.append(render_tag("div", styles={"font-size": theme_map["body_small_size"], "color": theme_map["metric_label_color"], "font-family": theme_map["font_family"]}, children=[label]))
        if detail is not None:
            children.append(render_tag("div", styles={"margin-top": "4px", "font-size": theme_map["body_small_size"], "color": theme_map["metric_detail_color"], "font-family": theme_map["font_family"]}, children=[detail]))
        if trend is not None:
            is_negative = str(trend).startswith("-")
            children.append(
                render_tag(
                    "div",
                    styles={"margin-top": theme_map["gap_sm"]},
                    children=[
                        render_tag(
                            "span",
                            styles={
                                "display": "inline-block",
                                "padding": "6px 10px",
                                "border-radius": theme_map["radius_pill"],
                                "background": theme_map["metric_trend_negative_background"] if is_negative else theme_map["metric_trend_positive_background"],
                                "color": theme_map["metric_trend_negative_color"] if is_negative else theme_map["metric_trend_positive_color"],
                                "font-size": theme_map["body_small_size"],
                                "font-weight": "700",
                                "font-family": theme_map["font_family"],
                            },
                            children=[trend],
                        )
                    ],
                )
            )
        super().__init__(*[raw(child) for child in children], **kwargs)


class ImageGroup(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        items: Sequence[ImageSpec],
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        columns: int = 2,
        gap: str | None = None,
        masonry: bool = False,
        feature_first: bool = False,
        **kwargs: object,
    ) -> None:
        if theme is None:
            deferred_items = list(items)
            self._deferred_factory = lambda: ImageGroup(
                deferred_items,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                columns=columns,
                gap=gap,
                masonry=masonry,
                feature_first=feature_first,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        item_gap = _resolve_gap(theme_map, gap, "image_grid_gap")
        groups: list[list[object]] = [[] for _ in range(max(columns, 1))]
        ordered = require_spec_sequence(list(items), ImageSpec, "items")
        if feature_first and len(ordered) > 1:
            groups[0].append(Image(ordered[0].src, alt=ordered[0].alt, theme=theme, theme_overrides=theme_overrides))
            ordered = ordered[1:]
        for index, item in enumerate(ordered):
            column = index % len(groups) if masonry else index // max(1, (len(ordered) + len(groups) - 1) // len(groups))
            column = min(column, len(groups) - 1)
            groups[column].append(Image(item.src, alt=item.alt, theme=theme, theme_overrides=theme_overrides))
        column_nodes = []
        for group in groups:
            column_nodes.append(Stack(*group, theme=theme, theme_overrides=theme_overrides, gap=item_gap))
        super().__init__(Columns(*column_nodes, gap=item_gap, widths=[f"{int(100 / len(column_nodes))}%" for _ in column_nodes]), **kwargs)


class LogoStrip(DeferredComponent):
    tag = "div"

    def __init__(
        self,
        items: Sequence[LogoSpec],
        *,
        theme: str | dict[str, object] | None = None,
        theme_overrides: dict[str, object] | None = None,
        boxed: bool = False,
        outlined: bool = False,
        columns: int | None = None,
        **kwargs: object,
    ) -> None:
        if theme is None:
            deferred_items = list(items)
            self._deferred_factory = lambda: LogoStrip(
                deferred_items,
                theme=_resolved_theme(theme_overrides),
                theme_overrides=None,
                boxed=boxed,
                outlined=outlined,
                columns=columns,
                **_deferred_kwargs(kwargs, theme_overrides),
            )
            return
        theme_map = build_theme(theme, theme_overrides)
        nodes: list[object] = []
        for item in require_spec_sequence(items, LogoSpec, "items"):
            label = item.label
            src = item.src
            if src:
                node: object = render_tag("img", attrs={"src": src, "alt": label}, styles={"height": "28px", "display": "block", "margin": "0 auto"})
                node = raw(node)
            else:
                node = Text(label, theme=theme, theme_overrides=theme_overrides, size="small", styles={"font-weight": "700", "color": theme_map["heading_color"]})
            if boxed or outlined:
                border = f"1px solid {theme_map['border_color']}" if outlined or boxed else "0"
                background = theme_map["muted_surface_color"] if boxed else "transparent"
                node = Surface(node, theme=theme, theme_overrides=theme_overrides, tone="ghost", padding="10px 14px", radius=theme_map["radius_sm"], border=border, background_color=background)
            nodes.append(node)
        if columns:
            column_nodes = [Stack(*nodes[index::columns], theme=theme, theme_overrides=theme_overrides, gap=theme_map["gap_sm"]) for index in range(columns)]
            super().__init__(Columns(*column_nodes, gap=theme_map["gap_md"]), **kwargs)
            return
        super().__init__(Inline(*nodes, theme=theme, theme_overrides=theme_overrides, gap=theme_map["gap_md"], wrap=True), **kwargs)
