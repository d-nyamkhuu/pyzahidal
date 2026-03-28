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

Generate or refresh the docs with:

```bash
python -m scripts.docs
```

The unified command runs docs generation, screenshot capture, and `mkdocs build` in the correct order.

Use `python -m scripts.docs --no-screenshots` or `python -m scripts.docs --no-build` when you want a partial refresh.

The generation stage writes:

- `docs/generated/components.md`
- `docs/generated/examples.md`
- `docs/generated/templates.md`
- `docs/generated/themes.md`
- `docs/generated/api-inventory.json`
- `docs/assets/examples/*.html`

The generated reference pages include constructor signatures, options, code snippets, and rendered previews. The authored guide pages stay separate from generated build artifacts.
