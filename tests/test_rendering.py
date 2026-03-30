from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyzahidal import (
    ActionSpec,
    Avatar,
    AvatarSpec,
    AvatarGroup,
    BlogPostSpec,
    Button,
    CallToAction,
    Columns,
    DataTable,
    DataColumnSpec,
    EmailDocument,
    FAQ,
    FaqItemSpec,
    Footer,
    Header,
    Heading,
    Hero,
    IconLink,
    ImageGroup,
    ImageSpec,
    Inline,
    JinjaExpr,
    LogoSpec,
    LogoCloud,
    LogoStrip,
    MarketingTemplate,
    Menu,
    MenuItemSpec,
    Metric,
    MetricSpec,
    NewsletterTemplate,
    OrderSummary,
    Pill,
    Pricing,
    PricingPlanSpec,
    ProductSpec,
    ProductList,
    ProductAnnouncementTemplate,
    PromoTemplate,
    ReviewSpec,
    Reviews,
    SocialLinkSpec,
    SocialLinks,
    Stack,
    Stats,
    Surface,
    Team,
    TeamMemberSpec,
    THEMES,
    Text,
    Timeline,
    TimelineStepSpec,
    WelcomeHero,
    build_theme,
    jinja,
    raw,
)
from scripts.generate_docs import _build_curated_component

class FakeDataFrame:
    def __init__(self, records):
        self.records = records

    def to_dict(self, orient="records"):
        if orient != "records":
            raise AssertionError(f"unexpected orient: {orient}")
        return self.records


def test_button_renders_link():
    html = Button("Buy now", href="https://example.com").render()
    assert 'href="https://example.com"' in html
    assert "Buy now" in html


def test_avatar_group_renders_overlapped_avatars():
    html = AvatarGroup(
        [
            AvatarSpec("https://example.com/a.png", alt="A"),
            AvatarSpec("https://example.com/b.png", alt="B"),
            AvatarSpec("https://example.com/c.png", alt="C"),
        ],
        size="44px",
        overlap="12px",
    ).render()
    assert "a.png" in html
    assert "b.png" in html
    assert "c.png" in html
    assert "margin-left:-12px" in html


def test_jinja_markup_is_preserved_with_raw():
    html = EmailDocument(
        sections=[
            Hero(
                eyebrow="Launch",
                title=raw("{{ headline }}"),
                body="Body",
                primary_action=ActionSpec("Open", href="#"),
            )
        ]
    ).render()
    assert "{{ headline }}" in html
    assert "&lt;table" not in html


def test_jinja_helper_wraps_expressions():
    expr = jinja("customer.first_name")
    assert isinstance(expr, JinjaExpr)
    assert expr.value == "{{ customer.first_name }}"


def test_render_template_preserves_jinja_in_text_and_attributes():
    html = EmailDocument(
        sections=[
            Hero(
                eyebrow=jinja("campaign.eyebrow"),
                title=jinja("campaign.title"),
                body=jinja("campaign.body"),
                primary_action=ActionSpec("Open", href=jinja("campaign.url")),
            )
        ],
        preview_text=jinja("campaign.preview"),
    ).render_template()
    assert "{{ campaign.title }}" in html
    assert 'href="{{ campaign.url }}"' in html
    assert "{{ campaign.preview }}" in html


def test_nested_components_render_real_html():
    html = Hero(eyebrow="Launch", title="Title", body="Body", primary_action=ActionSpec("Open", href="#")).render()
    assert "<td" in html
    assert "&lt;td" not in html


def test_hero_without_media_renders_single_column_layout():
    html = Hero(eyebrow="Launch", title="Title", body="Body", primary_action=ActionSpec("Open", href="#")).render()
    assert "width:100%; padding:" in html
    assert "width:42%" not in html


def test_document_renders_real_nested_markup():
    html = EmailDocument(sections=[Hero(eyebrow="Launch", title="Title", body="Body", primary_action=ActionSpec("Open", href="#"))]).render()
    assert "<body" in html
    assert "<table" in html
    assert "&lt;table" not in html


def test_document_shell_escapes_title_and_lang():
    html = EmailDocument(
        sections=["Hello"],
        title='<script>alert("x")</script>',
        lang='en" onclick="evil()',
    ).render()
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert 'onclick="evil()"' not in html
    assert 'lang="en&quot; onclick=&quot;evil()"' in html


def test_plain_text_is_still_escaped_without_raw():
    html = Hero(eyebrow="Launch", title="<script>alert(1)</script>", body="Body", primary_action=ActionSpec("Open", href="#")).render()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_data_table_renders_headers_and_rows():
    html = DataTable(headers=["Item", "Qty"], rows=[["Pen", 2]]).render()
    assert "<th" in html
    assert "Pen" in html
    assert "Qty" in html


def test_data_table_accepts_column_schema_and_mapping_rows():
    html = DataTable(
        columns=[
            DataColumnSpec("item", "Item"),
            DataColumnSpec("qty", "Qty", align="right"),
        ],
        rows=[{"item": "Pen", "qty": 2}],
        compact=True,
        theme="default",
    ).render()
    assert "Item" in html
    assert "Pen" in html
    assert "text-align:right" in html
    assert "padding:8px 10px" in html


def test_data_table_preserves_renderable_cells():
    html = DataTable(
        columns=[
            DataColumnSpec("status", "Status"),
            DataColumnSpec("action", "Action"),
        ],
        rows=[
            {
                "status": Pill("Healthy", tone="success", theme="default"),
                "action": Button("Edit", href="#", variant="ghost", theme="default"),
            }
        ],
        striped=True,
        theme="default",
    ).render()
    assert "Healthy" in html
    assert "Edit" in html
    assert 'href="#"' in html


def test_data_table_accepts_headers_with_list_of_dict_rows():
    html = DataTable(headers=["item", "qty"], rows=[{"item": "Pen", "qty": 2}]).render()
    assert "item" in html
    assert "Pen" in html
    assert "2" in html


def test_data_table_accepts_dataframe_like_rows():
    html = DataTable(
        columns=[
            DataColumnSpec("item", "Item"),
            DataColumnSpec("qty", "Qty"),
        ],
        rows=FakeDataFrame([{"item": "Pen", "qty": 2}]),
    ).render()
    assert "Item" in html
    assert "Pen" in html
    assert "Qty" in html


def test_data_table_requires_headers_or_columns():
    with pytest.raises(ValueError, match="headers or columns"):
        DataTable(rows=[["Pen", 2]]).render()


def test_data_table_rejects_short_rows():
    with pytest.raises(ValueError, match="expected 2"):
        DataTable(headers=["Item", "Qty"], rows=[["Pen"]]).render()


def test_data_table_rejects_extra_cells():
    with pytest.raises(ValueError, match="expected 1"):
        DataTable(headers=["Item"], rows=[["Pen", 2]]).render()


def test_data_table_rejects_duplicate_column_keys():
    with pytest.raises(ValueError, match="must be unique"):
        DataTable(columns=[DataColumnSpec("item", "Item"), DataColumnSpec("item", "Label")], rows=[{"item": "Pen"}]).render()


def test_theme_override_precedence():
    theme = build_theme("default", {"primary_color": "#000000"})
    assert theme["primary_color"] == "#000000"


def test_new_theme_presets_are_available():
    assert "editorial" in THEMES
    assert "vibrant" in THEMES
    assert THEMES["default"]["heading_font_family"]


def test_new_theme_tokens_can_be_overridden():
    theme = build_theme("editorial", {"button_radius": "4px", "eyebrow_background": "#123456"})
    assert theme["button_radius"] == "4px"
    assert theme["eyebrow_background"] == "#123456"


def test_marketing_template_renders_document_shell():
    html = MarketingTemplate(brand="Acme", hero_title="Hello", hero_body="Welcome", cta_label="Start").render()
    assert html.startswith("<!doctype html>")
    assert "Hello" in html
    assert "Acme" in html
    assert "Higher click-through" in html


def test_newsletter_template_renders_posts():
    html = NewsletterTemplate(
        brand="Acme",
        posts=[BlogPostSpec("Post 1", "Summary", href="#")],
    ).render()
    assert "Post 1" in html
    assert "Summary" in html
    assert "Weekly editorial dispatch" in html


def test_promo_template_renders_coupon_and_pricing():
    html = PromoTemplate(
        brand="Acme",
        code="SAVE20",
        detail="Use this today",
        plans=[
            PricingPlanSpec("Pro", "$20", "Best for teams", features=["Unlimited seats"], featured=True, action=ActionSpec("Choose plan", href="#", variant="primary"))
        ],
    ).render()
    assert "SAVE20" in html
    assert "Best for teams" in html
    assert "Unlimited seats" in html


def test_product_announcement_template_renders_product_data():
    html = ProductAnnouncementTemplate(
        brand="Acme",
        product=ProductSpec("Desk Lamp", "$49", "Warm light", features=["Low-profile base"]),
        related=[ProductSpec("Bulb", "$9", "Spare")],
    ).render()
    assert "Desk Lamp" in html
    assert "Bulb" in html
    assert "Low-profile base" in html


def test_product_announcement_template_uses_product_cta_configuration():
    html = ProductAnnouncementTemplate(
        brand="Acme",
        product=ProductSpec(
            "Desk Lamp",
            "$49",
            "Warm light",
            href="{{ product_url }}",
            label="See details",
            action=ActionSpec("See details", href="{{ product_url }}", variant="secondary"),
        ),
        related=[],
    ).render_template()
    assert "See details" in html
    assert 'href="{{ product_url }}"' in html


def test_product_announcement_template_skips_empty_optional_sections():
    template = ProductAnnouncementTemplate(
        brand="Acme",
        product=ProductSpec("Desk Lamp", "$49", "Warm light"),
        related=[],
    )
    assert len(template.sections) == 3


def test_order_summary_progress_bar_is_included():
    html = OrderSummary(rows=[("Subtotal", "$40"), ("Total", "$45")], progress=50, theme="vibrant").render()
    assert "Subtotal" in html
    assert "width:50%" in html
    assert f"background:{THEMES['vibrant']['primary_color']}" in html


def test_pricing_renders_multiple_plans_and_featured_state():
    html = Pricing(
        plans=[
            PricingPlanSpec("Starter", "$9", "Entry", features=["Docs"], action=ActionSpec("Choose starter", href="#", variant="secondary")),
            PricingPlanSpec("Scale", "$29", "Growth", features=["Priority support"], badge="Popular", featured=True, action=ActionSpec("Choose scale", href="#", variant="primary")),
        ]
    ).render()
    assert "Starter" in html
    assert "Scale" in html
    assert "Popular" in html
    assert "Priority support" in html
    assert THEMES["default"]["card_featured_border_color"] in html


def test_themed_button_uses_theme_tokens():
    html = Button("Buy now", href="#", theme="editorial").render()
    assert f"background:{THEMES['editorial']['primary_color']}" in html
    assert f"border-radius:{THEMES['editorial']['button_radius']}" in html


def test_document_theme_inherits_into_plain_primitive_sections():
    html = EmailDocument(sections=[Button("Buy now", href="#")], theme="editorial").render()
    assert f"background:{THEMES['editorial']['primary_color']}" in html
    assert f"border-radius:{THEMES['editorial']['button_radius']}" in html


def test_document_theme_inherits_into_nested_composite_sections():
    html = EmailDocument(
        sections=[Hero(eyebrow="Launch", title="Title", body="Body", primary_action=ActionSpec("Open", href="#"))],
        theme="editorial",
    ).render()
    assert f"background:{THEMES['editorial']['eyebrow_background']}" in html
    assert f"color:{THEMES['editorial']['muted_text_color']}" in html
    assert f"background:{THEMES['editorial']['primary_color']}" in html


def test_explicit_child_theme_beats_document_theme():
    html = EmailDocument(
        sections=[Button("Buy now", href="#", theme="commerce")],
        theme="modern",
    ).render()
    assert f"background:{THEMES['commerce']['primary_color']}" in html
    assert f"border-radius:{THEMES['commerce']['button_radius']}" in html


def test_child_theme_overrides_apply_on_inherited_document_theme():
    html = EmailDocument(
        sections=[Button("Buy now", href="#", theme_overrides={"primary_color": "#123456"})],
        theme="modern",
    ).render()
    assert "background:#123456" in html
    assert f"border-radius:{THEMES['modern']['button_radius']}" in html


def test_standalone_component_without_theme_still_uses_default_theme():
    html = Button("Buy now", href="#").render()
    assert f"background:{THEMES['default']['primary_color']}" in html
    assert f"border-radius:{THEMES['default']['button_radius']}" in html


def test_themed_hero_uses_theme_tokens():
    html = Hero(eyebrow="Launch", title="Title", body="Body", primary_action=ActionSpec("Open", href="#"), theme="editorial").render()
    assert f"background:{THEMES['editorial']['eyebrow_background']}" in html
    assert f"color:{THEMES['editorial']['muted_text_color']}" in html


def test_themed_data_table_uses_border_tokens():
    html = DataTable(headers=["Item", "Qty"], rows=[["Pen", 2]], theme="vibrant").render()
    assert f"border-bottom:1px solid {THEMES['vibrant']['table_header_border_color']}" in html
    assert f"border-bottom:1px solid {THEMES['vibrant']['table_row_border_color']}" in html


def test_status_pills_use_theme_status_tokens():
    html = "".join(
        [
            Pill("Healthy", tone="success", theme="default").render(),
            Pill("Churn risk", tone="warning", theme="default").render(),
            Pill("At risk", tone="danger", theme="default").render(),
        ]
    )
    assert THEMES["default"]["pill_success_background"] in html
    assert THEMES["default"]["pill_warning_background"] in html
    assert THEMES["default"]["pill_danger_background"] in html


def test_document_theme_reaches_template_sections():
    html = MarketingTemplate(brand="Acme", hero_title="Hello", hero_body="Welcome", cta_label="Start", theme="editorial").render()
    assert "font-family:Georgia" in html
    assert f"background:{THEMES['editorial']['eyebrow_background']}" in html


def test_call_to_action_renders_multiple_actions():
    html = CallToAction("Ready", "Choose a path.", [ActionSpec("Primary", href="#", variant="primary"), ActionSpec("Secondary", href="#", variant="ghost")]).render()
    assert "Primary" in html
    assert "Secondary" in html


def test_stats_accept_spec_items():
    html = Stats([MetricSpec(label="Open rate", value="51%", detail="Last 5 sends")]).render()
    assert "Open rate" in html
    assert "Last 5 sends" in html


def test_timeline_renders_changelog_fields():
    html = Timeline(
        [
            TimelineStepSpec("v1.0.9", "19 Jan", "Refactoring", "Refined layouts", "Introduced a new timeline pattern.")
        ]
    ).render()
    assert "v1.0.9" in html
    assert "19 Jan" in html
    assert "Refactoring" in html
    assert "Refined layouts" in html


def test_timeline_rejects_non_spec_inputs():
    try:
        Timeline([{"title": "Design", "detail": "Lock examples"}]).render()
    except TypeError as exc:
        assert "TimelineStepSpec" in str(exc)
        return
    raise AssertionError("Expected TypeError for non-spec changelog fields")


def test_curated_social_mapping_keeps_heading_body_and_icon_labels():
    component = _build_curated_component(
        "Social",
        "Simple social logos row",
        "default",
        {
            "headings": ["Connect with us"],
            "paragraphs": ["Stay in the loop by following us across our social channels."],
            "links": [{"href": "https://example.com", "label": "Visit profile"}],
            "images": [{"src": "https://example.com/linkedin.png", "alt": "LinkedIn"}],
            "prices": [],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
        },
    )
    html = component.render()
    assert "Connect with us" in html
    assert "Stay in the loop" in html
    assert "LinkedIn" in html


def test_curated_avatar_mapping_prefers_paragraph_name_and_email():
    component = _build_curated_component(
        "Avatars",
        "Avatar with details",
        "default",
        {
            "headings": [],
            "paragraphs": ["John Adams", "johnadams@example.com"],
            "links": [],
            "images": [{"src": "https://example.com/john.png", "alt": ""}],
            "prices": [],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
        },
    )
    html = component.render()
    assert "John Adams" in html
    assert "johnadams@example.com" in html


def test_curated_category_preview_mapping_keeps_card_titles_price_and_cta():
    component = _build_curated_component(
        "Category Previews",
        "Category preview with cards",
        "commerce",
        {
            "headings": ["Our products", "Sweatshirts", "Pants"],
            "paragraphs": ["Style meets purpose in every piece.", "$40.00-69.00", "$70.00-120.00"],
            "links": [{"href": "https://example.com", "label": "Shop now"}],
            "images": [{"src": "https://example.com/one.jpg", "alt": ""}, {"src": "https://example.com/two.jpg", "alt": ""}],
            "prices": ["$40.00", "$70.00"],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
        },
    )
    html = component.render()
    assert "Our products" in html
    assert "Sweatshirts" in html
    assert "$40.00-69.00" in html
    assert "Shop now" in html


def test_curated_avatar_mapping_uses_avatar_group_for_multiple_images():
    component = _build_curated_component(
        "Avatars",
        "Grouped overlapped avatars",
        "default",
        {
            "headings": ["Our community"],
            "paragraphs": ["Join the designers and builders already inside."],
            "links": [],
            "images": [
                {"src": "https://example.com/a.png", "alt": "A"},
                {"src": "https://example.com/b.png", "alt": "B"},
                {"src": "https://example.com/c.png", "alt": "C"},
            ],
            "prices": [],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
            "groups": [],
            "layout": "centered",
            "layout_flags": {"button_count": 0, "card_count": 1, "has_split_columns": False, "has_grid": False, "has_table": False, "small_image_count": 3, "table_columns": 0, "table_rows": 0},
        },
    )
    html = component.render()
    assert "margin-left:-16px" in html
    assert "Join the designers" in html


def test_curated_images_mapping_uses_image_group_when_multiple_images():
    component = _build_curated_component(
        "Images",
        "2 columns masonry image grid with 4 images",
        "modern",
        {
            "headings": ["Gallery"],
            "paragraphs": ["Explore the latest visuals."],
            "links": [],
            "images": [
                {"src": "https://example.com/1.png", "alt": "One"},
                {"src": "https://example.com/2.png", "alt": "Two"},
                {"src": "https://example.com/3.png", "alt": "Three"},
                {"src": "https://example.com/4.png", "alt": "Four"},
            ],
            "prices": [],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
            "groups": [],
            "layout": "grid",
            "layout_flags": {"button_count": 0, "card_count": 4, "has_split_columns": False, "has_grid": True, "has_table": False, "small_image_count": 0, "table_columns": 0, "table_rows": 0},
        },
    )
    html = component.render()
    assert html.count("<img") == 4
    assert "width:50%" in html


def test_curated_data_table_mapping_renders_action_buttons_without_repr_leaks():
    component = _build_curated_component(
        "Data Tables",
        "With logos and action links",
        "default",
        {
            "headings": ["Integrations"],
            "paragraphs": ["Manage your connected tools."],
            "links": [
                {"href": "https://example.com/manage/github", "label": "Manage"},
                {"href": "https://example.com/manage/linear", "label": "Manage"},
            ],
            "images": [
                {"src": "https://example.com/logo.png", "alt": "Logo"},
                {"src": "https://example.com/github.png", "alt": "GitHub"},
                {"src": "https://example.com/linear.png", "alt": "Linear"},
            ],
            "prices": [],
            "percents": [],
            "versions": [],
            "dates": [],
            "table_headers": [],
            "table_rows": [],
            "groups": [],
            "layout": "table",
            "layout_flags": {"button_count": 2, "card_count": 2, "has_split_columns": False, "has_grid": False, "has_table": True, "small_image_count": 3, "table_columns": 0, "table_rows": 0},
        },
    )
    html = component.render()
    assert "GitHub" in html
    assert "Linear" in html
    assert "Button(tag=" not in html


def test_welcome_hero_renders_centered_invite_content():
    html = WelcomeHero(
        title="The team welcomes you!",
        body="Your workspace is ready — confirm your email to join your team, collaborate seamlessly, and get started today.",
        action=ActionSpec("Confirm your email", href="#"),
        members=[
            AvatarSpec("https://example.com/a.png", alt="Avery", name="Avery"),
            AvatarSpec("https://example.com/b.png", alt="Nina", name="Nina"),
            AvatarSpec("https://example.com/c.png", alt="Kai", name="Kai"),
            AvatarSpec("https://example.com/d.png", alt="Lena", name="Lena"),
        ],
        theme="modern",
    ).render()
    assert "The team welcomes you!" in html
    assert "Confirm your email" in html
    assert "workspace is ready" in html
    assert "text-align:center" in html
    assert "margin-left:-12px" in html


def test_surface_supports_background_image_markup():
    html = Surface("Body", padding="24px", background_image="https://example.com/bg.png", theme="modern").render()
    assert "background-image:url(&#x27;https://example.com/bg.png&#x27;)" in html
    assert "padding:24px" in html


def test_surface_overlay_tone_uses_overlay_tokens():
    html = Surface("Body", tone="overlay", padding="24px", theme="modern").render()
    assert f"background:{THEMES['modern']['background_overlay_color']}" in html
    assert "rgba(255, 255, 255, 0.12)" in html


def test_curated_style_composition_builds_overlay_hero_shell():
    html = EmailDocument(
        sections=[
            Surface(
                Surface(
                    Stack(
                        Heading("Your upgrade starts here!", level="hero", tone="inverse", align="center", theme="modern"),
                        Text(
                            "Step into the next generation of innovation. Sleek design, pro-level performance, and features that keep you ahead of the curve.",
                            tone="inverse",
                            align="center",
                            theme="modern",
                        ),
                        Inline(
                            Button(
                                "Sign up now",
                                href="#",
                                theme="modern",
                                theme_overrides={"primary_color": "#5b5cf0", "primary_text_color": "#ffffff"},
                            ),
                            Button(
                                "Discover more",
                                href="#",
                                variant="ghost",
                                styles={"color": "#ffffff", "border": "1px solid #ffffff"},
                                theme="modern",
                            ),
                            align="center",
                            gap="16px",
                            theme="modern",
                        ),
                        gap="20px",
                        theme="modern",
                    ),
                    tone="overlay",
                    padding="56px 44px",
                    radius="12px",
                    theme="modern",
                ),
                background_image="https://example.com/iphone.jpg",
                background_color="#1f2937",
                padding="30px",
                radius="24px",
                theme="modern",
            )
        ],
        theme="modern",
    ).render()
    assert "iphone.jpg" in html
    assert THEMES["modern"]["background_overlay_color"] in html
    assert "Your upgrade starts here!" in html
    assert "Sign up now" in html
    assert "Discover more" in html
    assert "text-align:center" in html


def test_ghost_button_can_be_overridden_for_overlay_readability():
    html = Button(
        "Discover more",
        href="#",
        variant="ghost",
        styles={"color": "#ffffff", "border": "1px solid #ffffff"},
        theme="modern",
    ).render()
    assert "color:#ffffff" in html
    assert "border:1px solid #ffffff" in html


def test_stack_renders_consistent_vertical_spacing():
    html = Stack("One", "Two", gap="12px", theme="default").render()
    assert "One" in html
    assert "Two" in html
    assert "height:12px" in html


def test_columns_accept_explicit_widths():
    html = Columns("Main", "Side", widths=["65%", "35%"]).render()
    assert "width:65%" in html
    assert "width:35%" in html


def test_columns_default_vertical_alignment_stays_top():
    html = Columns("Main", "Side").render()
    assert "vertical-align:top" in html


def test_columns_accept_custom_vertical_alignment():
    html = Columns("Main", "Side", vertical_align="middle").render()
    assert "vertical-align:middle" in html


def test_columns_stack_on_mobile_emits_responsive_markup():
    html = Columns("Main", "Side", stack_on_mobile=True).render()
    assert "@media only screen and (max-width: 600px)" in html
    assert "pz-stack-mobile-2-16px" in html
    assert "width:50%" in html
    assert "display:block !important" in html
    assert "padding-bottom:16px !important" in html


def test_metric_renders_label_detail_and_trend_chip():
    html = Metric("55k", label="API calls", detail="This month", trend="+25%", theme="modern").render()
    assert "55k" in html
    assert "API calls" in html
    assert "+25%" in html
    assert THEMES["modern"]["metric_trend_positive_background"] in html


def test_menu_renders_navigation_links():
    html = Menu([MenuItemSpec("Docs", href="#docs"), MenuItemSpec("Pricing", href="#pricing")], theme="modern").render()
    assert "#docs" in html
    assert "Pricing" in html


def test_icon_link_renders_icon_tile():
    html = IconLink("#", "https://example.com/icon.png", alt="Docs", theme="modern").render()
    assert 'href="#"' in html
    assert "icon.png" in html
    assert THEMES["modern"]["social_tile_background"] in html
    assert 'role="presentation"' in html
    assert "valign:middle" not in html
    assert 'valign="middle"' in html
    assert "height:40px" in html


def test_social_links_icon_mode_supports_spec_items():
    html = SocialLinks(
        [SocialLinkSpec(href="#github", icon_src="https://example.com/github.png", alt="GitHub")],
        mode="icon",
        theme="default",
    ).render()
    assert "#github" in html
    assert "github.png" in html


def test_image_group_supports_masonry_composition():
    html = ImageGroup(
        [
            ImageSpec("https://example.com/one.png", alt="One"),
            ImageSpec("https://example.com/two.png", alt="Two"),
            ImageSpec("https://example.com/three.png", alt="Three"),
        ],
        columns=2,
        masonry=True,
        theme="modern",
    ).render()
    assert "one.png" in html
    assert "two.png" in html
    assert "three.png" in html


def test_logo_strip_supports_boxed_text_logos():
    html = LogoStrip([LogoSpec("Northwind"), LogoSpec("Acme")], boxed=True, theme="default").render()
    assert "Northwind" in html
    assert THEMES["default"]["muted_surface_color"] in html


def test_logo_cloud_uses_single_padded_surface():
    html = LogoCloud([LogoSpec("Northwind"), LogoSpec("Acme")], theme="default").render()
    assert "Northwind" in html
    assert "Acme" in html
    assert f"padding:{THEMES['default']['content_padding']}" in html
    assert "padding:0" not in html


def test_curated_style_composition_builds_split_hero_shell():
    html = EmailDocument(
        sections=[
            Surface(
                Columns(
                    Stack(
                        "Toothpaste",
                        "Salt.",
                        "Dusk | French Vanilla",
                        Button("Starts at $12.99", href="#", theme="commerce"),
                        gap="16px",
                        theme="commerce",
                    ),
                    Surface("", tone="ghost", background_image="https://example.com/hero.jpg", padding="140px 0", theme="commerce"),
                    widths=["52%", "48%"],
                    gap="18px",
                ),
                padding="24px",
                theme="commerce",
            )
        ],
        theme="commerce",
    ).render()
    assert "hero.jpg" in html
    assert "Starts at $12.99" in html
    assert "width:52%" in html


def test_curated_style_footer_can_be_composed_from_primitives():
    html = Surface(
        Stack(
            Columns(
                Stack("Acme Studio", "Quick links", Menu([MenuItemSpec("About", href="#"), MenuItemSpec("Shop", href="#")], theme="default"), gap="8px", theme="default"),
                Stack("Follow us", SocialLinks([SocialLinkSpec(href="#", icon_src="https://example.com/icon.png", alt="X")], mode="icon", theme="default"), gap="8px", align="right", theme="default"),
                widths=["60%", "40%"],
            ),
            Metric("$35.98", label="Amount charged", detail="Visa ****6754", theme="default"),
            gap="20px",
            theme="default",
        ),
        padding="24px",
        tone="subtle",
        theme="default",
    ).render()
    assert "Quick links" in html
    assert "Amount charged" in html
    assert "icon.png" in html


def test_header_supports_logo_tagline_and_meta_overrides():
    html = Header(
        "Acme Studio",
        nav_items=[MenuItemSpec("Docs", href="#docs"), MenuItemSpec("Pricing", href="#pricing")],
        logo_src="https://example.com/logo.png",
        logo_alt="Acme logo",
        tagline="Composable email components",
        meta_label="Navigation",
        theme="default",
    ).render()
    assert "logo.png" in html
    assert "Composable email components" in html
    assert "Navigation" in html
    assert "#docs" in html


def test_footer_supports_background_image_menu_and_legal_rows():
    html = Footer(
        "Acme Studio",
        social_items=[SocialLinkSpec(label="X", href="#x"), SocialLinkSpec(label="GitHub", href="#github")],
        top_image_src="https://example.com/footer.jpg",
        top_image_alt="Footer background",
        description="Source-driven footer copy.",
        menu_items=[MenuItemSpec("About", href="#about"), MenuItemSpec("Contact", href="#contact")],
        legal_links=[MenuItemSpec("Privacy", href="#privacy"), MenuItemSpec("Terms", href="#terms")],
        disclaimer="You can unsubscribe at any time.",
        theme="default",
    ).render()
    assert "footer.jpg" in html
    assert "Source-driven footer copy." in html
    assert "#about" in html
    assert "#privacy" in html
    assert "unsubscribe" in html


def test_faq_accepts_spec_items():
    html = FAQ(
        [
            FaqItemSpec("Can we use placeholders?", "Yes, via raw() where needed."),
            FaqItemSpec("Can we override tokens?", "Yes, with theme_overrides."),
        ],
        theme="default",
    ).render()
    assert "Can we use placeholders?" in html
    assert "theme_overrides" in html


def test_team_accepts_src_alias_and_action_metadata():
    html = Team(
        [
            TeamMemberSpec(
                name="Avery",
                role="Design",
                image="https://example.com/avery.png",
                meta="Product Team",
                action=ActionSpec("View profile", href="#avery"),
            )
        ],
        theme="default",
    ).render()
    assert "avery.png" in html
    assert "Product Team" in html
    assert "#avery" in html


def test_product_list_accepts_rich_product_metadata():
    html = ProductList(
        [
            ProductSpec(
                "Desk Lamp",
                "$49",
                "Warm light.",
                image_src="https://example.com/lamp.jpg",
                badge="Popular",
                rating="4.8",
                reviews="(18 reviews)",
                action=ActionSpec("Discover", href="#lamp", variant="primary"),
            )
        ],
        theme="commerce",
    ).render()
    assert "lamp.jpg" in html
    assert "Popular" in html
    assert "(18 reviews)" in html
    assert "#lamp" in html


def test_reviews_accept_rich_review_metadata():
    html = Reviews(
        [
            ReviewSpec(
                quote="Great quality and fast shipping.",
                author="Mia P.",
                src="https://example.com/mia.jpg",
                rating="★★★★★",
                action=ActionSpec("Read full review", href="#review"),
            )
        ],
        theme="editorial",
    ).render()
    assert "mia.jpg" in html
    assert "★★★★★" in html
    assert "Read full review" in html
