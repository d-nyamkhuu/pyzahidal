from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable


VOID_TAGS = {"img", "br", "hr", "meta", "link"}


class Markup(str):
    pass


@dataclass(frozen=True)
class Raw:
    value: str


@dataclass(frozen=True)
class JinjaExpr:
    value: str


def raw(value: str) -> Raw:
    return Raw(value=value)


def jinja(value: str) -> JinjaExpr:
    stripped = value.strip()
    if stripped.startswith(("{{", "{%", "{#")):
        return JinjaExpr(value=value)
    return JinjaExpr(value=f"{{{{ {value} }}}}")


def join_styles(*styles: dict[str, object] | None) -> str:
    pairs: list[str] = []
    for style_map in styles:
        if not style_map:
            continue
        for key, value in style_map.items():
            if value is None:
                continue
            css_key = key.replace("_", "-")
            pairs.append(f"{css_key}:{value}")
    return "; ".join(pairs)


def _attr_value_to_html(value: object, *, template_mode: bool = False) -> str:
    if isinstance(value, JinjaExpr):
        return value.value
    return escape(str(value), quote=True)


def attrs_to_html(
    attrs: dict[str, object] | None = None,
    styles: dict[str, object] | None = None,
    *,
    template_mode: bool = False,
) -> str:
    rendered: list[str] = []
    if attrs:
        for key, value in attrs.items():
            if value is None or value is False:
                continue
            if value is True:
                rendered.append(key)
                continue
            rendered.append(f'{key}="{_attr_value_to_html(value, template_mode=template_mode)}"')
    style_text = join_styles(styles)
    if style_text:
        rendered.append(f'style="{escape(style_text, quote=True)}"')
    return f" {' '.join(rendered)}" if rendered else ""


def render_fragment(value: object, *, template_mode: bool = False) -> str:
    if value is None:
        return ""
    if isinstance(value, Markup):
        return str(value)
    if template_mode and hasattr(value, "render_template") and callable(value.render_template):
        return Markup(value.render_template())
    if hasattr(value, "render") and callable(value.render):
        return Markup(value.render())
    if isinstance(value, Raw):
        return Markup(value.value)
    if isinstance(value, JinjaExpr):
        return Markup(value.value)
    if isinstance(value, (list, tuple)):
        return "".join(render_fragment(item, template_mode=template_mode) for item in value)
    return escape(str(value))


def render_tag(
    tag: str,
    *,
    attrs: dict[str, object] | None = None,
    styles: dict[str, object] | None = None,
    children: Iterable[object] | None = None,
    template_mode: bool = False,
) -> str:
    attr_html = attrs_to_html(attrs, styles, template_mode=template_mode)
    if tag in VOID_TAGS:
        return Markup(f"<{tag}{attr_html}/>")
    inner = "".join(render_fragment(child, template_mode=template_mode) for child in (children or []))
    return Markup(f"<{tag}{attr_html}>{inner}</{tag}>")
