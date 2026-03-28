# Core Concepts

## The mental model

`pyzahidal` has three main layers:

- `EmailDocument`: the outer document shell for the email, with title, preview text, language, and theme handling
- sections: larger building blocks such as `Hero`, `Header`, `Footer`, `Pricing`, `OrderSummary`, and `ProductList`
- primitives: lower-level layout and content pieces such as `Section`, `Stack`, `Columns`, `Text`, `Button`, and `Divider`

Most custom emails start with `EmailDocument`, then a small number of sections, then primitives when you need more control.

## Templates vs custom composition

Starter templates are the fastest way to ship a complete email:

- `MarketingTemplate`
- `NewsletterTemplate`
- `PromoTemplate`
- `ProductAnnouncementTemplate`
- `OrderTemplate`

Use them when the built-in flow is already close to what you need.

Custom composition is the better path when you want to:

- mix sections from different email types
- inject custom layout primitives between sections
- control spacing, grouping, or repeated content more precisely

## Rendering and templating

Plain strings are escaped by default. That keeps accidental HTML or script content from leaking into the output.

Use:

- `raw()` when you want to keep literal markup or template syntax untouched
- `jinja()` when you want a simple Jinja expression wrapped for you
- `render()` for final HTML
- `render_template()` for Jinja-ready HTML

## Themes

Every component accepts a `theme` preset name or theme tokens.

Built-in presets include:

- `default`
- `editorial`
- `vibrant`
- `modern`
- `commerce`

Use `theme_overrides` when you want to keep a preset but change a few tokens such as colors or radius values.

See [Themes](generated/themes.md) for the token reference and side-by-side previews.

## How to navigate the reference

- Use [Examples](generated/examples.md) when you know the outcome you want.
- Use [Components](generated/components.md) when you know the building block you want.
- Use [Templates](generated/templates.md) when you want a complete starting layout.
