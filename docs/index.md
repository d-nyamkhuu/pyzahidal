# Start Here

`pyzahidal` helps you build HTML emails from composable Python components instead of hand-authoring large table-based templates.

It is a good fit when you want:

- a fast way to ship email layouts from Python
- Jinja-friendly output for your own template pipeline
- reusable sections like heroes, pricing, carts, order summaries, and footers
- starter templates that you can use immediately and customize later

## First path

If you are new to the library, start here:

1. Install the package and render your first email in [Quickstart](quickstart.md).
2. Learn the mental model in [Core Concepts](core-concepts.md).
3. Browse [Examples](generated/examples.md) by use case once you know what you want to build.

## Common use cases

- Product announcements: hero, CTA, features, pricing, testimonials
- Newsletters: header, editorial blocks, blog lists, footers
- Promotions: coupon, pricing, banners, urgency copy
- Ecommerce: product detail, product lists, cart, order summary
- Utility layouts: navigation, stats, tables, alerts, dividers

## Choose your starting point

### I want a working email quickly

Use a starter template such as `MarketingTemplate`, `NewsletterTemplate`, `PromoTemplate`, `ProductAnnouncementTemplate`, or `OrderTemplate`.

Go to [Quickstart](quickstart.md) and then [Templates](generated/templates.md).

### I want full control over layout

Start with `EmailDocument`, then compose sections and primitives like `Hero`, `Section`, `Stack`, `Text`, `Button`, and `Footer`.

Go to [Core Concepts](core-concepts.md) and then [Components](generated/components.md).

### I want examples I can adapt

Use the curated examples page, which groups real previews by user goal instead of raw component category names.

Go to [Examples](generated/examples.md).

## What the docs cover

- authored onboarding guides for first-time users
- generated reference for every public component and starter template
- curated examples with code, previews, and screenshots
- theme presets and override examples

## Maintainer workflows

For GitHub Actions setup, PyPI/TestPyPI secrets, and the exact git tag commands used for releases, see [Publishing](publishing.md).
