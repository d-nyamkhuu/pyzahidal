# pyzahidal

Composable Python components for building HTML emails with Jinja-friendly output.

`pyzahidal` is designed for teams that want reusable email building blocks instead of maintaining large hand-written HTML templates.

## What you get

- Email-safe primitives such as sections, stacks, columns, buttons, tables, alerts, avatars, and spacing
- Reusable sections such as heroes, pricing, blog lists, product lists, carts, order summaries, and footers
- Starter templates for common marketing, editorial, promotion, product, and order flows
- Theme presets with token overrides
- Jinja-friendly rendering via `raw()`, `jinja()`, and `render_template()`

## Install

From PyPI:

```bash
pip install pyzahidal
```

From a checkout:

```bash
pip install -e .
```

Or run directly from the repository:

```bash
PYTHONPATH=src python your_script.py
```

## First example

```python
from pyzahidal import ActionSpec, EmailDocument, Hero

email = EmailDocument(
    preview_text="Composable emails with Jinja output",
    sections=[
        Hero(
            eyebrow="Launch week",
            title="Build emails from reusable sections",
            body="Start with a document shell, add sections, then customize only what you need.",
            primary_action=ActionSpec("Explore", href="https://example.com/docs"),
        )
    ]
)

html = email.render()
```

`html` is a complete HTML email document.

When you want template expressions preserved, use `raw()`, `jinja()`, and `render_template()`.

## Documentation

The docs are organized for first-time users first:

- `Start Here`: library overview and where to begin
- `Quickstart`: first working email and Jinja-safe rendering
- `Core Concepts`: document shell, sections, primitives, themes, and templates
- `Recipes`: common paths like marketing, newsletter, promo, and ecommerce emails
- `Examples`: curated previews grouped by use case
- `Reference`: generated component, template, and theme reference
