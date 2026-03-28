# Quickstart

This page gets you from install to a rendered email as quickly as possible.

## Install

```bash
pip install -e .
```

If you are running from a checkout without installation:

```bash
PYTHONPATH=src python your_script.py
```

## Render your first email

```python
from pyzahidal import ActionSpec, EmailDocument, Hero

email = EmailDocument(
    preview_text="Composable emails with Jinja-friendly output",
    sections=[
        Hero(
            eyebrow="Launch week",
            title="Ship email layouts from Python",
            body="Build sections, not giant HTML tables.",
            primary_action=ActionSpec("Explore docs", href="https://example.com/docs"),
        )
    ],
)

html = email.render()
```

`html` is a complete HTML email document. Save it to an `.html` file or open it in a preview tool to inspect the output.

## Use Jinja placeholders safely

When you want placeholders to stay unescaped:

```python
from pyzahidal import ActionSpec, EmailDocument, Hero, jinja, raw

email = EmailDocument(
    preview_text=jinja("campaign.preview"),
    sections=[
        Hero(
            eyebrow=jinja("campaign.eyebrow"),
            title=raw("{{ campaign.title }}"),
            body=jinja("campaign.body"),
            primary_action=ActionSpec("Open", href=jinja("campaign.url")),
        )
    ],
)

html = email.render_template()
```

Use:

- `render()` when your content is already final
- `render_template()` when you want Jinja expressions preserved
- `raw()` for literal template fragments
- `jinja()` for simple `{{ ... }}` expressions

## Choose your next step

- Use [Core Concepts](core-concepts.md) if you want to understand how the library is organized.
- Use [Examples](generated/examples.md) if you want to start from a similar real-world layout.
- Use [Templates](generated/templates.md) if you want a starter flow instead of composing everything yourself.
