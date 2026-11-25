"""Generate a 12-slide widescreen PowerPoint presentation for the SereneMind Mental Health Chatbot System."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PPTX = ROOT / "Mental_Health_Chatbot_Presentation.pptx"
HOME_IMG = Path("/tmp/pro5_slide_home.png")
CHAT_IMG = Path("/tmp/pro5_slide_chat.png")

# Design palette matching SereneMind
BG_LINEN = RGBColor(0xF5, 0xF7, 0xF3)
DARK_SAGE = RGBColor(0x1F, 0x4A, 0x42)
SAGE_PRIMARY = RGBColor(0x2B, 0x67, 0x5C)
SAGE_MID = RGBColor(0x3D, 0x7D, 0x70)
SAGE_SOFT = RGBColor(0xE3, 0xF0, 0xEC)
CARD_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CARD_ALT = RGBColor(0xFA, 0xFB, 0xF9)
BORDER_COLOR = RGBColor(0xDC, 0xE4, 0xDC)
TEXT_MAIN = RGBColor(0x1C, 0x29, 0x25)
TEXT_MUTED = RGBColor(0x58, 0x6A, 0x64)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MINT_LIGHT = RGBColor(0xC7, 0xE3, 0xDC)

POS_BG = RGBColor(0xE3, 0xF5, 0xEA)
POS_FG = RGBColor(0x1B, 0x6B, 0x3A)
NEU_BG = RGBColor(0xE9, 0xEE, 0xF2)
NEU_FG = RGBColor(0x3B, 0x53, 0x66)
NEG_BG = RGBColor(0xFB, 0xEA, 0xEA)
NEG_FG = RGBColor(0x9F, 0x2D, 0x2D)

FONT_FAMILY = "Calibri"
TOTAL_SLIDES = 12


def set_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    fill_color: RGBColor,
    line_color: RGBColor | None = None,
    line_width: float = 1.0,
    rounded: bool = False,
):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    if rounded and hasattr(shape, "adjustments") and len(shape.adjustments) > 0:
        shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color is not None:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()
    return shape


def add_textbox(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    font_size: int = 13,
    bold: bool = False,
    color: RGBColor = TEXT_MAIN,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    margin: float = 0.04,
):
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT_FAMILY
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_bullets(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    items: list[tuple[str, str] | str],
    font_size: int = 12,
    color: RGBColor = TEXT_MUTED,
    lead_color: RGBColor = TEXT_MAIN,
    space_after: int = 6,
):
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)

    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = 1.15
        if isinstance(item, tuple):
            lead, body = item
            r_bullet = p.add_run()
            r_bullet.text = "•  "
            r_bullet.font.name = FONT_FAMILY
            r_bullet.font.size = Pt(font_size)
            r_bullet.font.bold = True
            r_bullet.font.color.rgb = SAGE_PRIMARY

            r_lead = p.add_run()
            r_lead.text = f"{lead}: "
            r_lead.font.name = FONT_FAMILY
            r_lead.font.size = Pt(font_size)
            r_lead.font.bold = True
            r_lead.font.color.rgb = lead_color

            r_body = p.add_run()
            r_body.text = body
            r_body.font.name = FONT_FAMILY
            r_body.font.size = Pt(font_size)
            r_body.font.color.rgb = color
        else:
            r_bullet = p.add_run()
            r_bullet.text = f"•  {item}"
            r_bullet.font.name = FONT_FAMILY
            r_bullet.font.size = Pt(font_size)
            r_bullet.font.color.rgb = color
    return box


def add_chrome(
    slide,
    slide_num: int,
    kicker: str,
    title: str,
    subtitle: str = "",
) -> None:
    set_bg(slide, BG_LINEN)
    # Top accent strip
    add_rect(slide, 0, 0, 13.333, 0.08, DARK_SAGE)
    # Kicker
    add_textbox(
        slide, 0.65, 0.24, 9.0, 0.28, kicker.upper(), font_size=10, bold=True, color=SAGE_PRIMARY
    )
    # Title
    add_textbox(
        slide, 0.65, 0.48, 12.0, 0.48, title, font_size=24, bold=True, color=TEXT_MAIN
    )
    if subtitle:
        add_textbox(
            slide, 0.65, 0.96, 12.0, 0.34, subtitle, font_size=12, color=TEXT_MUTED
        )
    # Subtle footer divider
    add_rect(slide, 0.65, 7.05, 12.033, 0.015, BORDER_COLOR)
    add_textbox(
        slide,
        0.65,
        7.10,
        8.0,
        0.28,
        "SereneMind  ·  Mental Health Chatbot System",
        font_size=9.5,
        color=TEXT_MUTED,
    )
    add_textbox(
        slide,
        11.2,
        7.10,
        1.48,
        0.28,
        f"{slide_num:02d} / {TOTAL_SLIDES}",
        font_size=9.5,
        bold=True,
        color=SAGE_PRIMARY,
        align=PP_ALIGN.RIGHT,
    )


def build_slide_01(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DARK_SAGE)

    # Geometric sage accents on right
    circle1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.2), Inches(-0.9), Inches(5.1), Inches(5.1))
    circle1.fill.solid()
    circle1.fill.fore_color.rgb = SAGE_PRIMARY
    circle1.line.fill.background()

    circle2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.3), Inches(3.7), Inches(3.8), Inches(3.8))
    circle2.fill.solid()
    circle2.fill.fore_color.rgb = RGBColor(0x25, 0x5A, 0x50)
    circle2.line.fill.background()

    # Right mini preview card
    preview = add_rect(slide, 8.35, 1.55, 4.3, 4.35, CARD_WHITE, rounded=True)
    preview.line.fill.background()
    live_dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.60), Inches(1.82), Inches(0.14), Inches(0.14))
    live_dot.fill.solid()
    live_dot.fill.fore_color.rgb = RGBColor(0x27, 0xA8, 0x66)
    live_dot.line.fill.background()
    add_textbox(slide, 8.82, 1.74, 3.5, 0.3, "SereneMind Therapist Companion", font_size=11, bold=True, color=SAGE_PRIMARY)
    add_rect(slide, 8.6, 2.15, 3.8, 0.015, BORDER_COLOR)

    u_box = add_rect(slide, 9.25, 2.35, 3.15, 0.72, SAGE_PRIMARY, rounded=True)
    u_box.line.fill.background()
    add_textbox(slide, 9.38, 2.41, 2.9, 0.6, '"I feel anxious and overwhelmed with exams today."', font_size=10, color=WHITE)

    pill = add_rect(slide, 10.65, 3.18, 1.75, 0.28, NEG_BG, rounded=True)
    pill.line.fill.background()
    add_textbox(slide, 10.65, 3.18, 1.75, 0.28, "Negative · Anxiety", font_size=9, bold=True, color=NEG_FG, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)

    b_box = add_rect(slide, 8.6, 3.58, 3.45, 0.92, BG_LINEN, rounded=True)
    b_box.line.fill.background()
    add_textbox(slide, 8.72, 3.64, 3.2, 0.8, "Let's pause together. Try a 4-4-4-4 box breath right now — I've curated calming videos below.", font_size=10, color=TEXT_MAIN)

    v_box = add_rect(slide, 8.6, 4.65, 3.8, 0.95, SAGE_SOFT, rounded=True)
    v_box.line.fill.background()
    add_textbox(slide, 8.76, 4.74, 3.5, 0.28, "▶  Box Breathing Relaxation Technique", font_size=10.5, bold=True, color=DARK_SAGE, margin=0.02)
    add_textbox(slide, 8.76, 5.06, 3.5, 0.40, "Sunnybrook Hospital · 4 min · Matched for Anxiety", font_size=9.5, color=TEXT_MUTED, margin=0.02)

    # Left Hero Content
    kicker_pill = add_rect(slide, 0.75, 1.35, 3.35, 0.36, SAGE_MID, rounded=True)
    kicker_pill.line.fill.background()
    add_textbox(slide, 0.75, 1.35, 3.35, 0.36, "MENTAL HEALTH CHATBOT SYSTEM", font_size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)

    add_textbox(slide, 0.75, 1.92, 7.1, 1.45, "SereneMind:\nMental Health Chatbot App", font_size=38, bold=True, color=WHITE)
    add_textbox(
        slide,
        0.75,
        3.52,
        7.0,
        0.95,
        "A conversational therapist companion powered by Rasa NLU, real-time sentiment analysis, and curated mental-health video recommendations.",
        font_size=15,
        color=MINT_LIGHT,
    )

    # Tech Stack Pills (fit cleanly left of x=8.0)
    stack = ["HTML · CSS · JS", "Python · Flask", "Rasa 3.6 NLU", "MySQL / SQLite", "VADER Sentiment"]
    x_pos = 0.75
    for label in stack:
        w = 1.24 if len(label) < 14 else 1.40
        add_rect(slide, x_pos, 5.15, w, 0.38, RGBColor(0x2B, 0x67, 0x5C), MINT_LIGHT, line_width=0.75, rounded=True)
        add_textbox(slide, x_pos, 5.15, w, 0.38, label, font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
        x_pos += w + 0.11

    add_textbox(slide, 0.75, 6.65, 7.0, 0.35, "Project Presentation  ·  Full-Stack Conversational AI & Behavioral Health Support", font_size=10.5, color=MINT_LIGHT)


def build_slide_02(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        2,
        "Background & Problem Statement",
        "Closing the Mental Health Access Gap",
        "Global mental health care faces severe workforce shortages and social stigma barriers.",
    )

    # Left featured stat card
    stat_card = add_rect(slide, 0.65, 1.52, 4.45, 5.15, DARK_SAGE, rounded=True)
    stat_card.line.fill.background()
    add_textbox(slide, 0.95, 1.82, 3.85, 0.32, "WORLD HEALTH ORGANIZATION", font_size=10, bold=True, color=MINT_LIGHT)
    add_textbox(slide, 0.95, 2.28, 3.85, 1.35, "~70%", font_size=68, bold=True, color=WHITE)
    add_textbox(
        slide,
        0.95,
        3.78,
        3.85,
        1.15,
        "of individuals needing mental health interventions have no access to trained professional services.",
        font_size=15,
        color=WHITE,
    )
    add_rect(slide, 0.95, 5.18, 3.85, 0.02, SAGE_MID)
    add_textbox(
        slide,
        0.95,
        5.36,
        3.85,
        1.05,
        "Scalable conversational systems can bridge this gap with immediate, affordable, and stigma-free emotional support.",
        font_size=11.5,
        color=MINT_LIGHT,
    )

    # Right 3 stacked cards
    cards = [
        (
            "Global Shortage of Trained Workers",
            "Healthcare systems worldwide lack enough trained mental health professionals to deliver timely, personalized behavioral interventions.",
        ),
        (
            "Reluctance Due to Stigmatization",
            "Many individuals experiencing mental distress avoid seeking clinical advice because of fear of judgment or social stigma.",
        ),
        (
            "Chatbots as a Scalable Solution",
            "Conversational agents communicate naturally via written, spoken, and visual cues—offering economical, 24/7 empathetic guidance.",
        ),
    ]
    y = 1.52
    for heading, desc in cards:
        add_rect(slide, 5.4, y, 7.28, 1.56, CARD_WHITE, BORDER_COLOR, rounded=True)
        add_rect(slide, 5.4, y, 0.12, 1.56, SAGE_PRIMARY)
        add_textbox(slide, 5.75, y + 0.22, 6.65, 0.36, heading, font_size=15, bold=True, color=TEXT_MAIN)
        add_textbox(slide, 5.75, y + 0.62, 6.65, 0.78, desc, font_size=12.5, color=TEXT_MUTED)
        y += 1.79


def build_slide_03(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        3,
        "Proposed Solution & Objectives",
        "How SereneMind Supports Every User",
        "An interactive therapist-style chatbot analyzing emotional expressions and recommending tailored video therapy.",
    )

    cards = [
        (
            "01",
            "Real-Time Therapist Companion",
            "Behaves like an attentive conversational companion that validates feelings, offers practical grounding cues, and responds empathetically at every turn.",
        ),
        (
            "02",
            "Rasa NLU Intent Understanding",
            "Powered by Python and Rasa NLU to accurately classify user expressions across 16 mental-health, conversational, and help-seeking intents.",
        ),
        (
            "03",
            "Positive · Neutral · Negative Detection",
            "Evaluates emotional polarity, fine-grained emotion tags (anxiety, stress, sadness, gratitude), and multi-turn communication trends.",
        ),
        (
            "04",
            "Curated Video Recommendations",
            "Matches verified YouTube guided meditations, breathing exercises, and TED talks directly to the user's detected emotional state.",
        ),
    ]

    coords = [(0.65, 1.55), (6.80, 1.55), (0.65, 4.25), (6.80, 4.25)]
    for (num, heading, body), (cx, cy) in zip(cards, coords):
        add_rect(slide, cx, cy, 5.88, 2.42, CARD_WHITE, BORDER_COLOR, rounded=True)
        badge = add_rect(slide, cx + 0.28, cy + 0.28, 0.56, 0.42, SAGE_SOFT, rounded=True)
        badge.line.fill.background()
        add_textbox(slide, cx + 0.28, cy + 0.28, 0.56, 0.42, num, font_size=13, bold=True, color=SAGE_PRIMARY, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
        add_textbox(slide, cx + 1.0, cy + 0.30, 4.6, 0.4, heading, font_size=16, bold=True, color=TEXT_MAIN)
        add_textbox(slide, cx + 0.28, cy + 0.90, 5.3, 1.25, body, font_size=12.5, color=TEXT_MUTED)


def build_slide_04(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        4,
        "Technical Architecture",
        "End-to-End 4-Tier System Design",
        "Modular separation across the web frontend, Flask API layer, Rasa NLU engine, and MySQL persistence.",
    )

    tiers = [
        (
            "1. Frontend",
            "HTML5 · CSS3 · JavaScript",
            SAGE_SOFT,
            SAGE_PRIMARY,
            [
                ("Auth Views", "Register & Login forms with validation"),
                ("Chat UI", "Session history, sentiment pills, typing state"),
                ("Video Modal", "Embedded YouTube player + library filter"),
                ("Visuals", "SVG mood sparkline & Web Speech dictation"),
            ],
        ),
        (
            "2. Backend",
            "Python · Flask (:5000)",
            CARD_WHITE,
            SAGE_PRIMARY,
            [
                ("Auth Blueprint", "Werkzeug password hashing & session guard"),
                ("Chat API", "/api/chat, /api/sessions, /api/analytics"),
                ("RasaClient", "REST webhook & /model/parse integration"),
                ("Resilience", "Local TF-IDF NLU fallback when offline"),
            ],
        ),
        (
            "3. AI Engine",
            "Rasa (:5005) & Actions (:5055)",
            CARD_WHITE,
            SAGE_PRIMARY,
            [
                ("NLU Pipeline", "DIETClassifier + FallbackClassifier"),
                ("Policies", "Memoization, RulePolicy & TEDPolicy"),
                ("Custom Actions", "ActionTherapistSentimentResponse"),
                ("Shared Engine", "VADER + mental-health lexicon + crisis guard"),
            ],
        ),
        (
            "4. Database",
            "MySQL (PyMySQL) / SQLite",
            SAGE_SOFT,
            DARK_SAGE,
            [
                ("Schema", "users, chat_sessions, chat_messages"),
                ("Analytics", "sentiment_logs with trend tracking"),
                ("Video Catalog", "15 curated YouTube mental-health resources"),
                ("Auto Mode", "MySQL primary with local SQLite fallback"),
            ],
        ),
    ]

    x = 0.65
    card_w = 2.74
    gap = 0.35
    for idx, (tier_title, tier_sub, bg, hdr_color, bullets) in enumerate(tiers):
        add_rect(slide, x, 1.55, card_w, 5.10, bg, BORDER_COLOR, rounded=True)
        add_rect(slide, x, 1.55, card_w, 0.88, hdr_color, rounded=False)
        add_textbox(slide, x + 0.16, 1.62, card_w - 0.32, 0.36, tier_title, font_size=15, bold=True, color=WHITE)
        add_textbox(slide, x + 0.16, 1.98, card_w - 0.32, 0.32, tier_sub, font_size=10.5, color=MINT_LIGHT)
        add_bullets(slide, x + 0.16, 2.62, card_w - 0.32, 3.85, bullets, font_size=11, space_after=10)

        if idx < len(tiers) - 1:
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                Inches(x + card_w + 0.05),
                Inches(3.85),
                Inches(0.25),
                Inches(0.32),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = SAGE_PRIMARY
            arrow.line.fill.background()
        x += card_w + gap


def build_slide_05(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        5,
        "System Description",
        "User Module: Registration, Login & Chatbot Flow",
        "A streamlined single-module workflow designed for stigma-free onboarding and private emotional check-ins.",
    )

    steps = [
        (
            "STEP 01",
            "User Registration",
            "/register",
            [
                ("Basic Details", "Full name, username, email & password"),
                ("Validation", "Format checks & duplicate prevention"),
                ("Security", "Salted password hash via Werkzeug"),
                ("Storage", "Persisted in MySQL users table"),
            ],
        ),
        (
            "STEP 02",
            "Secure Login",
            "/login",
            [
                ("Credentials", "Username & password hash verification"),
                ("Session Cookie", "HttpOnly & SameSite=Lax protection"),
                ("Route Guard", "@login_required protects /chat & APIs"),
                ("Multi-Session", "Loads user's saved check-in threads"),
            ],
        ),
        (
            "STEP 03",
            "Start Chatbot",
            "/chat",
            [
                ("Interactive Chat", "Starter mood chips, text & voice input"),
                ("Sentiment Tag", "Positive, Negative or Neutral per turn"),
                ("Video Care", "Watch in modal or open on YouTube"),
                ("Pattern View", "Live mood bars & SVG trend sparkline"),
            ],
        ),
    ]

    x = 0.65
    w = 3.72
    gap = 0.43
    for idx, (badge_txt, title_txt, route_txt, items) in enumerate(steps):
        add_rect(slide, x, 1.55, w, 5.10, CARD_WHITE, BORDER_COLOR, rounded=True)
        b_shape = add_rect(slide, x + 0.25, 1.82, 1.05, 0.34, SAGE_PRIMARY, rounded=True)
        b_shape.line.fill.background()
        add_textbox(slide, x + 0.25, 1.82, 1.05, 0.34, badge_txt, font_size=9.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)

        r_shape = add_rect(slide, x + 2.45, 1.82, 1.02, 0.34, SAGE_SOFT, rounded=True)
        r_shape.line.fill.background()
        add_textbox(slide, x + 2.45, 1.82, 1.02, 0.34, route_txt, font_size=9.5, bold=True, color=SAGE_PRIMARY, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)

        add_textbox(slide, x + 0.25, 2.34, w - 0.5, 0.44, title_txt, font_size=18, bold=True, color=TEXT_MAIN)
        add_rect(slide, x + 0.25, 2.86, w - 0.5, 0.015, BORDER_COLOR)
        add_bullets(slide, x + 0.25, 3.08, w - 0.5, 3.3, items, font_size=12, space_after=12)

        if idx < 2:
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                Inches(x + w + 0.08),
                Inches(3.85),
                Inches(0.27),
                Inches(0.36),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = SAGE_PRIMARY
            arrow.line.fill.background()
        x += w + gap


def build_slide_06(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        6,
        "Conversational AI Engine",
        "Rasa 3.6 NLU Pipeline & Custom Therapist Actions",
        "Trained DIETClassifier + TEDPolicy model paired with custom Python actions for real-time emotional feedback.",
    )

    # Left Card: Pipeline
    add_rect(slide, 0.65, 1.52, 5.9, 5.15, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.92, 1.75, 5.35, 0.38, "NLU & Dialogue Pipeline (rasa_bot/config.yml)", font_size=15, bold=True, color=SAGE_PRIMARY)

    pipe_stages = [
        "1. WhitespaceTokenizer  +  Regex & LexicalSyntactic Featurizers",
        "2. CountVectorsFeaturizer  (word n-grams + char_wb 1–4)",
        "3. DIETClassifier  (60 epochs, intent classification)",
        "4. FallbackClassifier  (threshold 0.35 → therapist action)",
        "5. Policies: Memoization · RulePolicy · TEDPolicy (40 epochs)",
    ]
    py = 2.28
    for stage in pipe_stages:
        box = add_rect(slide, 0.92, py, 5.36, 0.46, SAGE_SOFT, rounded=True)
        box.line.fill.background()
        add_textbox(slide, 1.06, py, 5.1, 0.46, stage, font_size=11, bold=True, color=TEXT_MAIN, valign=MSO_ANCHOR.MIDDLE, margin=0)
        py += 0.56

    add_textbox(slide, 0.92, 5.22, 5.36, 0.3, "16 Trained NLU Intents (data/nlu.yml):", font_size=11, bold=True, color=TEXT_MAIN)
    add_textbox(
        slide,
        0.92,
        5.52,
        5.36,
        0.95,
        "greet · goodbye · affirm · deny · bot_challenge · thank_you · ask_help · mood_great · mood_neutral · mood_sad · mood_anxious · mood_stressed · mood_angry · sleep_issues · crisis_self_harm · request_video",
        font_size=10.5,
        color=TEXT_MUTED,
    )

    # Right Card: Custom Actions
    add_rect(slide, 6.82, 1.52, 5.86, 5.15, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 7.10, 1.75, 5.3, 0.38, "Custom Actions & Safety (actions/actions.py)", font_size=15, bold=True, color=SAGE_PRIMARY)

    actions = [
        (
            "ActionTherapistSentimentResponse",
            "Extracts conversation history from the Rasa tracker, computes sentiment & pattern trend, sets last_sentiment/last_emotion slots, and emits empathetic text + JSON metadata.",
        ),
        (
            "ActionRecommendVideo",
            "Responds to explicit video requests (request_video) using stored mood slots to deliver calming, mindful, or uplifting video links.",
        ),
        (
            "Crisis Safety Guardrail",
            "Detects self-harm phrases or crisis_self_harm intent immediately and surfaces 24/7 helplines (988, Text HOME to 741741, findahelpline.com).",
        ),
    ]
    ay = 2.30
    for a_title, a_desc in actions:
        add_rect(slide, 7.10, ay, 5.30, 1.30, CARD_ALT, BORDER_COLOR, rounded=True)
        add_rect(slide, 7.10, ay, 0.10, 1.30, SAGE_PRIMARY)
        add_textbox(slide, 7.32, ay + 0.12, 4.95, 0.32, a_title, font_size=12.5, bold=True, color=TEXT_MAIN)
        add_textbox(slide, 7.32, ay + 0.44, 4.95, 0.78, a_desc, font_size=10.5, color=TEXT_MUTED)
        ay += 1.46


def build_slide_07(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        7,
        "Sentiment & Pattern Engine",
        "Positive, Negative & Neutral Classification",
        "Shared hybrid analysis engine (shared/sentiment_engine.py) powering both Flask and Rasa actions.",
    )

    pillars = [
        (
            "POSITIVE",
            "Score  >=  +0.15",
            POS_BG,
            POS_FG,
            [
                ("Emotions", "Gratitude, happiness, calm, flourishing"),
                ("Bot Response", "Celebrates wins & reinforces positive habits"),
                ("Video Match", "Uplifting TED & positive-psychology talks"),
            ],
        ),
        (
            "NEUTRAL",
            "-0.15  <  Score  <  +0.15",
            NEU_BG,
            NEU_FG,
            [
                ("Emotions", "Mindfulness, self-reflection, steady check-in"),
                ("Greeting Filter", "Short hi/bye turns skip false positivity"),
                ("Video Match", "5–10 minute guided mindfulness resets"),
            ],
        ),
        (
            "NEGATIVE",
            "Score  <=  -0.15",
            NEG_BG,
            NEG_FG,
            [
                ("Emotions", "Anxiety, stress, sadness, anger, sleep, crisis"),
                ("Bot Response", "Validates pain + box breathing / grounding"),
                ("Video Match", "Anxiety relief, emotional first aid & sleep"),
            ],
        ),
    ]

    px = 0.65
    pw = 3.80
    for label, threshold, p_bg, p_fg, bullets in pillars:
        add_rect(slide, px, 1.52, pw, 3.55, CARD_WHITE, BORDER_COLOR, rounded=True)
        hdr = add_rect(slide, px + 0.22, 1.74, pw - 0.44, 0.72, p_bg, rounded=True)
        hdr.line.fill.background()
        add_textbox(slide, px + 0.22, 1.78, pw - 0.44, 0.34, label, font_size=14, bold=True, color=p_fg, align=PP_ALIGN.CENTER, margin=0)
        add_textbox(slide, px + 0.22, 2.12, pw - 0.44, 0.28, threshold, font_size=10.5, bold=True, color=p_fg, align=PP_ALIGN.CENTER, margin=0)
        add_bullets(slide, px + 0.24, 2.68, pw - 0.48, 2.25, bullets, font_size=11.5, space_after=10)
        px += pw + 0.31

    # Bottom pattern tracking strip
    strip = add_rect(slide, 0.65, 5.30, 12.03, 1.38, DARK_SAGE, rounded=True)
    strip.line.fill.background()
    add_textbox(slide, 0.92, 5.44, 11.4, 0.34, "Communication Pattern & Trajectory Analytics", font_size=14, bold=True, color=WHITE)
    add_textbox(
        slide,
        0.92,
        5.82,
        11.4,
        0.74,
        "•  Fuses VADER + 40+ mental-health lexicon weights with high-confidence Rasa intents (respecting negation like 'not happy').\n"
        "•  Tracks Positive / Neutral / Negative percentages, trajectory trend (initial, improving, declining, stable), and consecutive negative streaks.",
        font_size=11.5,
        color=MINT_LIGHT,
    )


def build_slide_08(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        8,
        "Data Layer & Video Curation",
        "MySQL Schema & Curated Video Repository",
        "Normalized 5-table relational database with PyMySQL, SQLite fallback, and 15 verified mental-health videos.",
    )

    # Left: Schema Table Card
    add_rect(slide, 0.65, 1.52, 6.20, 5.15, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.90, 1.74, 5.7, 0.36, "MySQL Schema (database/schema.sql)", font_size=15, bold=True, color=SAGE_PRIMARY)

    rows = [
        ("users", "Account identity, username/email uniqueness, password hash"),
        ("chat_sessions", "Per-user conversation threads & auto-derived titles"),
        ("chat_messages", "User/bot turns, sentiment, score, intent & video IDs"),
        ("sentiment_logs", "Chronological mood timeline & trend per session"),
        ("videos", "15 curated YouTube resources indexed by sentiment/emotion"),
    ]
    ry = 2.25
    for tbl_name, tbl_desc in rows:
        add_rect(slide, 0.90, ry, 5.70, 0.66, CARD_ALT, BORDER_COLOR, rounded=True)
        badge = add_rect(slide, 1.04, ry + 0.14, 1.55, 0.38, SAGE_SOFT, rounded=True)
        badge.line.fill.background()
        add_textbox(slide, 1.04, ry + 0.14, 1.55, 0.38, tbl_name, font_size=10.5, bold=True, color=SAGE_PRIMARY, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
        add_textbox(slide, 2.72, ry + 0.10, 3.76, 0.46, tbl_desc, font_size=10.5, color=TEXT_MUTED, valign=MSO_ANCHOR.MIDDLE)
        ry += 0.76

    add_textbox(slide, 0.90, 6.12, 5.70, 0.42, "DB_BACKEND=auto uses MySQL/XAMPP via PyMySQL and falls back to SQLite seamlessly.", font_size=10.5, bold=True, color=SAGE_PRIMARY)

    # Right: Video Distribution Card
    add_rect(slide, 7.12, 1.52, 5.56, 5.15, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 7.38, 1.74, 5.05, 0.36, "15 Verified YouTube Resources", font_size=15, bold=True, color=SAGE_PRIMARY)

    bars = [
        ("Negative / Calming", "8 videos  (Anxiety, Stress, Sadness, Anger, Sleep)", 0.92, NEG_FG, NEG_BG),
        ("Neutral / Mindful", "4 videos  (Mindfulness & Self-Reflection)", 0.50, NEU_FG, NEU_BG),
        ("Positive / Uplifting", "3 videos  (Gratitude, Happiness, Flourishing)", 0.38, POS_FG, POS_BG),
    ]
    by = 2.30
    for b_label, b_sub, ratio, fg, bg in bars:
        add_textbox(slide, 7.38, by, 5.05, 0.28, b_label, font_size=12, bold=True, color=TEXT_MAIN)
        add_textbox(slide, 7.38, by + 0.26, 5.05, 0.26, b_sub, font_size=10, color=TEXT_MUTED)
        track = add_rect(slide, 7.38, by + 0.56, 5.0, 0.24, bg, rounded=True)
        track.line.fill.background()
        fill_bar = add_rect(slide, 7.38, by + 0.56, 5.0 * ratio, 0.24, fg, rounded=True)
        fill_bar.line.fill.background()
        by += 1.00

    add_bullets(
        slide,
        7.38,
        5.36,
        5.05,
        1.15,
        [
            ("Emotion Prioritization", "Matches anxiety, stress, or sleep tags first"),
            ("No Repeats", "Excludes recently recommended videos in session"),
            ("Trusted Channels", "TED, TEDx, Calm, Goodful, Sunnybrook, City of Hope"),
        ],
        font_size=10.5,
        space_after=4,
    )


def build_slide_09(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        9,
        "Live Application Showcase",
        "Responsive Web Interface & Real-Time Mood Insights",
        "Actual rendered views of SereneMind showing the calming landing page and live sentiment-driven chat space.",
    )

    frames = [
        (
            0.65,
            "1. Landing & User Onboarding  (/)",
            "Clean hero, workflow steps, and direct Register / Log In navigation.",
            HOME_IMG,
        ),
        (
            6.80,
            "2. Therapist Chat & Mood Analytics  (/chat)",
            "Session sidebar, sentiment tags, inline video cards, and live SVG sparkline.",
            CHAT_IMG,
        ),
    ]

    for fx, f_title, f_sub, img_path in frames:
        add_rect(slide, fx, 1.50, 5.88, 5.20, CARD_WHITE, BORDER_COLOR, rounded=True)
        # Browser titlebar accent
        bar = add_rect(slide, fx, 1.50, 5.88, 0.36, SAGE_SOFT)
        bar.line.color.rgb = BORDER_COLOR
        add_textbox(slide, fx + 0.16, 1.52, 5.56, 0.32, f_title, font_size=11, bold=True, color=DARK_SAGE, valign=MSO_ANCHOR.MIDDLE, margin=0)

        if img_path.exists():
            # Image 1280x760 => aspect 1.684; fit inside width 5.58" => height 3.31"
            slide.shapes.add_picture(
                str(img_path),
                Inches(fx + 0.15),
                Inches(1.98),
                width=Inches(5.58),
            )
        add_textbox(slide, fx + 0.16, 5.52, 5.56, 0.95, f_sub, font_size=11.5, color=TEXT_MUTED)


def build_slide_10(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        10,
        "Methodology & Requirements",
        "Waterfall Project Life Cycle & System Requirements",
        "Sequential SDLC phases from requirements gathering to testing and deployment.",
    )

    # Top Waterfall SDLC strip
    add_rect(slide, 0.65, 1.50, 12.03, 2.38, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.90, 1.66, 11.5, 0.34, "Project Life Cycle — Classical Waterfall Model", font_size=14.5, bold=True, color=SAGE_PRIMARY)

    phases = [
        ("1. Requirements", "Mental health gap, user auth & video goals"),
        ("2. Analysis", "Sentiment classes & Rasa NLU intent scope"),
        ("3. Design", "4-tier Flask/Rasa architecture & MySQL schema"),
        ("4. Coding", "Python backend, Rasa actions & HTML/CSS/JS"),
        ("5. Testing", "Unit, DB, route & live E2E verification"),
        ("6. Implementation", "Startup script & live web deployment"),
    ]
    px = 0.88
    pw = 1.78
    for idx, (p_name, p_desc) in enumerate(phases):
        top_offset = 2.10 + (idx % 2) * 0.12
        box = add_rect(slide, px, top_offset, pw, 1.42, SAGE_SOFT if idx % 2 == 0 else CARD_ALT, BORDER_COLOR, rounded=True)
        add_rect(slide, px, top_offset, pw, 0.36, SAGE_PRIMARY)
        add_textbox(slide, px + 0.06, top_offset, pw - 0.12, 0.36, p_name, font_size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
        add_textbox(slide, px + 0.10, top_offset + 0.44, pw - 0.20, 0.88, p_desc, font_size=9.5, color=TEXT_MUTED, align=PP_ALIGN.CENTER)
        if idx < len(phases) - 1:
            arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(px + pw + 0.03), Inches(2.72), Inches(0.16), Inches(0.22))
            arr.fill.solid()
            arr.fill.fore_color.rgb = SAGE_PRIMARY
            arr.line.fill.background()
        px += pw + 0.22

    # Bottom Hardware & Software Cards
    add_rect(slide, 0.65, 4.12, 5.85, 2.58, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.92, 4.32, 5.3, 0.36, "Hardware Requirements (Laptop or PC)", font_size=15, bold=True, color=SAGE_PRIMARY)
    add_bullets(
        slide,
        0.92,
        4.76,
        5.3,
        1.75,
        [
            ("Operating System", "Windows 7 or higher, Linux, or macOS"),
            ("Processor", "Intel Core i3 or higher"),
            ("Memory", "4 GB RAM or higher"),
            ("Storage", "100 GB ROM / disk space or higher"),
        ],
        font_size=12,
        space_after=8,
    )

    add_rect(slide, 6.83, 4.12, 5.85, 2.58, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 7.10, 4.32, 5.3, 0.36, "Software & Technology Stack", font_size=15, bold=True, color=SAGE_PRIMARY)
    add_bullets(
        slide,
        7.10,
        4.76,
        5.3,
        1.75,
        [
            ("Backend & NLU", "Python 3.10, Flask 3.1, Rasa 3.6.21, VADER"),
            ("Frontend", "HTML5, CSS3, Vanilla JavaScript"),
            ("Database", "MySQL / XAMPP Server (PyMySQL) + SQLite fallback"),
            ("Tooling & QA", "Code Editor (Sublime / VS Code), Pytest"),
        ],
        font_size=12,
        space_after=8,
    )


def build_slide_11(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        11,
        "Verification, Advantages & Limitations",
        "Tested Results, Key Strengths & Future Scope",
        "Verified end-to-end across unit tests, database checks, and live Rasa + Flask execution.",
    )

    # Top 4 KPI cards
    kpis = [
        ("15 / 15", "Pytest Tests Passing", "Sentiment, DB, Routes & Rasa"),
        ("100%", "Live E2E Verified", "Rasa (:5005) + Actions + Flask"),
        ("16", "Trained NLU Intents", "Mood, Help, Video & Crisis"),
        ("15", "Verified YouTube Videos", "Positive, Neutral & Negative"),
    ]
    kx = 0.65
    kw = 2.82
    for val, lbl, sub in kpis:
        add_rect(slide, kx, 1.50, kw, 1.48, DARK_SAGE, rounded=True)
        add_textbox(slide, kx + 0.16, 1.62, kw - 0.32, 0.56, val, font_size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER, margin=0)
        add_textbox(slide, kx + 0.16, 2.20, kw - 0.32, 0.30, lbl, font_size=11.5, bold=True, color=MINT_LIGHT, align=PP_ALIGN.CENTER, margin=0)
        add_textbox(slide, kx + 0.16, 2.50, kw - 0.32, 0.32, sub, font_size=9.5, color=MINT_LIGHT, align=PP_ALIGN.CENTER, margin=0)
        kx += kw + 0.25

    # Bottom Left: Advantages
    add_rect(slide, 0.65, 3.24, 5.85, 3.45, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.92, 3.44, 5.3, 0.36, "Key Advantages", font_size=16, bold=True, color=POS_FG)
    add_bullets(
        slide,
        0.92,
        3.90,
        5.3,
        2.6,
        [
            ("Easy to Maintain", "Clean modular separation across Flask, Rasa & DB"),
            ("User-Friendly UI", "Calm theme, starter chips, modal video & voice input"),
            ("Real-Time Sentiment", "Detects positive, negative & neutral expressions accurately"),
            ("Video Therapy Links", "Recommends tailored mental-health videos with crisis safety"),
        ],
        font_size=11.5,
        space_after=10,
    )

    # Bottom Right: Limitations & Future Scope
    add_rect(slide, 6.83, 3.24, 5.85, 3.45, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 7.10, 3.44, 5.3, 0.36, "Limitations & Future Scope", font_size=16, bold=True, color=SAGE_PRIMARY)
    add_bullets(
        slide,
        7.10,
        3.90,
        5.3,
        2.6,
        [
            ("Current Limitation", "If a user does not clearly express their thoughts or feelings, sentiment accuracy decreases."),
            ("Multilingual NLU", "Expand Rasa training data to support regional languages."),
            ("Clinical Summaries", "Allow users to export anonymized mood-trend PDF reports."),
            ("Scheduled Check-Ins", "Optional daily wellness prompts and voice-synthesized replies."),
        ],
        font_size=11.5,
        space_after=10,
    )


def build_slide_12(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(
        slide,
        12,
        "References & Conclusion",
        "Research References & Live Demo",
        "Literature grounding conversational AI and sentiment tracking in behavioral health support.",
    )

    add_rect(slide, 0.65, 1.50, 12.03, 3.48, CARD_WHITE, BORDER_COLOR, rounded=True)
    add_textbox(slide, 0.92, 1.68, 11.4, 0.36, "Academic & Technical References", font_size=15, bold=True, color=SAGE_PRIMARY)

    refs = [
        "1.  JMIR Formative Research (2020) — Mental Health Chatbot Interventions: https://formative.jmir.org/2020/11/e17065/",
        "2.  ResearchGate — An Overview of the Features of Chatbots in Mental Health: A Scoping Review (Publication 336054143)",
        "3.  IOPscience — Journal of Physics Conference Series: https://iopscience.iop.org/article/10.1088/1742-6596/2161/1/012039/pdf",
        "4.  SSRN Research Paper — Mental Health Support Systems: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3768304",
        "5.  Academia.edu — Sentiment Analysis using Chatbot and Mental Health Tracker: https://www.academia.edu/79840155/",
    ]
    ry = 2.15
    for ref in refs:
        add_textbox(slide, 0.92, ry, 11.45, 0.44, ref, font_size=11, color=TEXT_MAIN)
        ry += 0.52

    # Closing Banner
    banner = add_rect(slide, 0.65, 5.20, 12.03, 1.55, DARK_SAGE, rounded=True)
    banner.line.fill.background()
    add_textbox(slide, 0.95, 5.36, 7.8, 0.56, "Thank You!  Questions & Live Demo", font_size=24, bold=True, color=WHITE)
    add_textbox(
        slide,
        0.95,
        5.98,
        8.2,
        0.55,
        "SereneMind Mental Health Chatbot System — Supporting mental well-being through accessible AI conversation.",
        font_size=12,
        color=MINT_LIGHT,
    )

    cmd_box = add_rect(slide, 8.95, 5.45, 3.45, 1.05, SAGE_PRIMARY, MINT_LIGHT, line_width=0.75, rounded=True)
    add_textbox(slide, 9.10, 5.54, 3.15, 0.28, "RUN LOCALLY", font_size=9.5, bold=True, color=MINT_LIGHT)
    add_textbox(slide, 9.10, 5.82, 3.15, 0.56, "./scripts/start_all.sh\nhttp://127.0.0.1:5000", font_size=11, bold=True, color=WHITE)


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    build_slide_01(prs)
    build_slide_02(prs)
    build_slide_03(prs)
    build_slide_04(prs)
    build_slide_05(prs)
    build_slide_06(prs)
    build_slide_07(prs)
    build_slide_08(prs)
    build_slide_09(prs)
    build_slide_10(prs)
    build_slide_11(prs)
    build_slide_12(prs)

    prs.save(str(OUTPUT_PPTX))
    print(f"Presentation saved to {OUTPUT_PPTX} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
