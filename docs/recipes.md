# Recipes

These are the most common ways new users approach the library.

## Build a marketing email

Start with `MarketingTemplate` if you want a fast launch path. Switch to `EmailDocument` plus `Hero`, `Feature`, `CallToAction`, and `Footer` if you need more control.

Best next pages:

- [Templates](generated/templates.md)
- [Examples](generated/examples.md#product-announcement)

## Build a newsletter

Use `NewsletterTemplate` for an editorial starting point, then customize `Header`, `BlogList`, `Text`, and `Footer`.

Best next pages:

- [Templates](generated/templates.md)
- [Examples](generated/examples.md#newsletter-and-editorial)

## Build a promo or campaign email

Use `PromoTemplate` or combine `Hero`, `Coupon`, `Pricing`, and supporting CTA sections.

Best next pages:

- [Examples](generated/examples.md#promotion-and-campaigns)
- [Themes](generated/themes.md)

## Build an ecommerce or order email

Use `OrderTemplate` or compose `ProductDetail`, `ProductList`, `ShoppingCart`, and `OrderSummary`.

Best next pages:

- [Examples](generated/examples.md#ecommerce-and-order-flows)
- [Components](generated/components.md)

## Inject Jinja variables

Use `jinja()` for expressions and `render_template()` for final output that should still contain template expressions.

Use `raw()` when you need to preserve more complex template fragments exactly.

Best next pages:

- [Quickstart](quickstart.md)
- [Core Concepts](core-concepts.md)

## Customize the visual style

Pick the nearest built-in theme first, then override tokens instead of rewriting each component style.

Best next pages:

- [Themes](generated/themes.md)
- [Examples](generated/examples.md)
