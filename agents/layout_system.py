"""
Layout System for Manim Scene Generation

Provides a grid-based positioning system with safe zones and spacing constants
to prevent text overlap and misalignment in dynamically generated scenes.

Based on research from:
- Manimator (arxiv.org/html/2507.14306v1) - Grid-based anchor points
- Code2Video (arxiv.org/pdf/2510.01174) - Constraint validation
"""

# ─── Grid Anchor Points ─────────────────────────────────────────────────────
# 3x3 grid for consistent element positioning
# These correspond to Manim's coordinate system (-7 to 7 horizontal, -4 to 4 vertical)

GRID_ANCHORS = {
    # Top row
    "top_left": "UP * 3 + LEFT * 5",
    "top_center": "UP * 3",
    "top_right": "UP * 3 + RIGHT * 5",
    # Middle row
    "center_left": "LEFT * 5",
    "center": "ORIGIN",
    "center_right": "RIGHT * 5",
    # Bottom row
    "bottom_left": "DOWN * 3 + LEFT * 5",
    "bottom_center": "DOWN * 3",
    "bottom_right": "DOWN * 3 + RIGHT * 5",
}

# ─── Safe Area Margins ──────────────────────────────────────────────────────
# Content should stay within these bounds to avoid being cut off
# Manim frame is typically 14.2 x 8 units (16:9 aspect ratio)

SAFE_AREA = {
    "left": -6.0,      # Keep content right of this
    "right": 6.0,      # Keep content left of this
    "top": 3.5,        # Keep content below this
    "bottom": -3.5,    # Keep content above this
    "width": 12.0,     # Maximum content width
    "height": 7.0,     # Maximum content height
}

# ─── Standard Font Sizes ────────────────────────────────────────────────────
# Consistent typography across scenes

FONT_SIZES = {
    "title": 44,           # Main title at top
    "subtitle": 32,        # Secondary title
    "heading": 30,         # Section headings
    "body": 26,            # Main content text
    "bullet": 24,          # Bullet point text
    "caption": 20,         # Small captions/labels
    "code": 22,            # Code/monospace text
}

# ─── Spacing Constants ──────────────────────────────────────────────────────
# Minimum spacing between elements to prevent overlap

SPACING = {
    "title_margin": 0.5,        # Space from top edge to title
    "title_content": 0.4,       # Space between title and content
    "line_height": 0.25,        # Space between text lines
    "bullet_spacing": 0.3,      # Space between bullet points
    "column_gap": 1.0,          # Space between columns
    "element_padding": 0.3,     # Padding around elements
    "section_gap": 0.5,         # Space between sections
    "edge_buffer": 0.5,         # Buffer from screen edges
}

# ─── Standardized Spacing Scale ────────────────────────────────────────────
# Consistent spacing values for Claude-style layouts

SPACING_SCALE = {
    "xs": 0.15,   # Tight spacing (within cards)
    "sm": 0.25,   # Small gaps (bullet spacing)
    "md": 0.4,    # Standard spacing (between elements)
    "lg": 0.6,    # Section gaps
    "xl": 0.8,    # Major sections
}

# ─── Claude-Style Color Palette ────────────────────────────────────────────
# Professional muted colors inspired by Claude's visual explanations

CLAUDE_COLORS = {
    # Backgrounds (dark theme)
    "bg_dark": "#1a1b26",        # Main scene background
    "bg_card": "#24283b",        # Card/box background
    "bg_card_alt": "#1f2335",    # Alternate card background
    "bg_header": "#16161e",      # Header section background

    # Semantic box colors (for Option A/B style comparisons)
    "option_a": "#364fc7",       # Blue for Option A / left side
    "option_a_light": "#4263eb", # Lighter blue for headers
    "option_b": "#2f9e44",       # Green for Option B / right side
    "option_b_light": "#40c057", # Lighter green for headers
    "recommend": "#0ca678",      # Teal for recommendation banners
    "recommend_dark": "#099268", # Darker teal for borders
    "warning": "#f59f00",        # Amber for warnings
    "error": "#e03131",          # Red for errors/cons

    # Text colors
    "text_primary": "#c0caf5",   # Main body text (soft white)
    "text_secondary": "#565f89", # Muted/secondary text
    "text_heading": "#7aa2f7",   # Heading blue
    "text_white": "#ffffff",     # Pure white for high contrast
    "text_dark": "#1a1b26",      # Dark text on light backgrounds

    # Border colors
    "border_subtle": "#3b4261",  # Subtle borders for cards
    "border_accent": "#7aa2f7",  # Accent borders (blue)

    # Status colors
    "success": "#9ece6a",        # Green checkmark
    "info": "#7dcfff",           # Info blue
}

# ─── Claude-Style Typography ───────────────────────────────────────────────
# Simplified font sizes for consistent visual hierarchy

CLAUDE_FONTS = {
    "title": 38,        # Main scene title
    "heading": 28,      # Section headers (Option A, Key Points, etc.)
    "body": 22,         # Content text
    "caption": 18,      # Small labels, captions
    "badge": 16,        # Badge/chip text
}

# ─── Layout Templates ───────────────────────────────────────────────────────
# Common layout patterns as positioning code snippets

LAYOUT_PATTERNS = {
    "title_at_top": """
title.to_edge(UP, buff={title_margin})
""".format(**SPACING),

    "content_below_title": """
content.next_to(title, DOWN, buff={title_content})
""".format(**SPACING),

    "bullet_list": """
bullets = VGroup(*bullet_texts)
bullets.arrange(DOWN, aligned_edge=LEFT, buff={bullet_spacing})
bullets.next_to(title, DOWN, buff={title_content})
""".format(**SPACING),

    "two_columns": """
left_col.to_edge(LEFT, buff=1.5)
right_col.to_edge(RIGHT, buff=1.5)
""",

    "centered_content": """
content.move_to(ORIGIN)
content.shift(DOWN * 0.5)  # Slightly below center for balance
""",

    "footer_at_bottom": """
footer.to_edge(DOWN, buff={edge_buffer})
""".format(**SPACING),
}

# ─── Layout Rules (for prompts) ─────────────────────────────────────────────
# These rules are injected into LLM prompts

LAYOUT_RULES_PROMPT = """
═══════════════════════════════════════════════════════════════════════════════
MANDATORY LAYOUT RULES - FOLLOW EXACTLY (prevents text overlap/misalignment)
═══════════════════════════════════════════════════════════════════════════════

RULE 1: STANDARD SCENE STRUCTURE (copy this pattern exactly)
────────────────────────────────────────────────────────────
```python
# Background first
bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
self.add(bg)

# Title at top - ALWAYS use to_edge(UP)
title = Text("Title Here", font_size=40, color=WHITE)
title.to_edge(UP, buff=0.5)

# Content group - ALWAYS use VGroup + arrange + next_to
content_items = VGroup(
    Text("Item 1", font_size=26),
    Text("Item 2", font_size=26),
    Text("Item 3", font_size=26),
)
content_items.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
content_items.next_to(title, DOWN, buff=0.6)

# Scale if needed
if content_items.get_width() > 11:
    content_items.scale_to_fit_width(11)
```

RULE 2: POSITIONING - USE ONLY THESE METHODS
────────────────────────────────────────────
✓ CORRECT:
  title.to_edge(UP, buff=0.5)
  subtitle.next_to(title, DOWN, buff=0.4)
  items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
  group.move_to(ORIGIN).shift(DOWN * 0.5)

✗ WRONG - NEVER DO THIS:
  text.move_to([3, 2, 0])     # Hardcoded coordinates cause misalignment
  text.move_to(UP * 4)         # Too far, goes off screen
  text.shift(LEFT * 7)         # Off screen

RULE 3: MULTIPLE TEXT ELEMENTS - ALWAYS GROUP
─────────────────────────────────────────────
When you have 2+ text elements, ALWAYS:
1. Create VGroup: items = VGroup(text1, text2, text3)
2. Arrange them: items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
3. Position relative to title: items.next_to(title, DOWN, buff=0.5)
4. Scale if needed: items.scale_to_fit_width(11)

RULE 4: SAFE BOUNDARIES (content MUST stay within)
──────────────────────────────────────────────────
- Maximum X position: -5.5 to +5.5 (NOT ±7)
- Maximum Y position: -3.0 to +3.2 (NOT ±4)
- Maximum content width: 11 units
- Maximum content height: 6 units

RULE 5: FONT SIZES (never exceed these)
───────────────────────────────────────
- Title: font_size=40-44
- Subtitle: font_size=30-32
- Body text: font_size=24-28
- Bullets/small: font_size=22-24
- NEVER use font_size > 44

RULE 6: MANDATORY SCALING FOR SAFETY
────────────────────────────────────
After creating content group, ALWAYS add:
```python
if main_group.get_width() > 11:
    main_group.scale_to_fit_width(11)
if main_group.get_height() > 6:
    main_group.scale_to_fit_height(6)
```
═══════════════════════════════════════════════════════════════════════════════
"""

# ─── Helper Functions ───────────────────────────────────────────────────────


def get_safe_font_size(text_length: int, max_width: float = 12.0) -> int:
    """Estimate appropriate font size based on text length."""
    if text_length < 20:
        return FONT_SIZES["title"]
    elif text_length < 40:
        return FONT_SIZES["heading"]
    elif text_length < 60:
        return FONT_SIZES["body"]
    else:
        return FONT_SIZES["bullet"]


def estimate_text_width(text: str, font_size: int) -> float:
    """Rough estimate of text width in Manim units."""
    # Approximate: each character is ~0.1 * font_size/48 units wide
    char_width = 0.1 * (font_size / 48)
    return len(text) * char_width


def will_text_overflow(text: str, font_size: int, max_width: float = 12.0) -> bool:
    """Check if text will exceed the safe area width."""
    estimated_width = estimate_text_width(text, font_size)
    return estimated_width > max_width


def suggest_scale_factor(text: str, font_size: int, max_width: float = 12.0) -> float:
    """Suggest a scale factor to fit text within max_width."""
    estimated_width = estimate_text_width(text, font_size)
    if estimated_width <= max_width:
        return 1.0
    return max_width / estimated_width


def get_layout_code_snippet(layout_type: str) -> str:
    """Get a code snippet for a specific layout pattern."""
    return LAYOUT_PATTERNS.get(layout_type, "")


# ─── Validation Helpers ─────────────────────────────────────────────────────


def check_position_in_safe_area(x: float, y: float) -> tuple[bool, str]:
    """Check if a position is within the safe area."""
    issues = []

    if x < SAFE_AREA["left"]:
        issues.append(f"x={x} is left of safe area (min: {SAFE_AREA['left']})")
    if x > SAFE_AREA["right"]:
        issues.append(f"x={x} is right of safe area (max: {SAFE_AREA['right']})")
    if y > SAFE_AREA["top"]:
        issues.append(f"y={y} is above safe area (max: {SAFE_AREA['top']})")
    if y < SAFE_AREA["bottom"]:
        issues.append(f"y={y} is below safe area (min: {SAFE_AREA['bottom']})")

    return len(issues) == 0, "; ".join(issues)


# ─── LaTeX Settings ────────────────────────────────────────────────────────────
# Font sizes and styling for mathematical content based on complexity

LATEX_FONT_SIZES = {
    # Simple equations (E=mc², a+b=c)
    "simple": {
        "font_size": 48,
        "max_symbols": 10,
        "description": "Basic equations, single variables",
    },
    # Medium complexity (fractions, subscripts, simple integrals)
    "medium": {
        "font_size": 40,
        "max_symbols": 25,
        "description": "Fractions, subscripts, simple integrals",
    },
    # Complex (nested fractions, summations, matrices)
    "complex": {
        "font_size": 32,
        "max_symbols": 50,
        "description": "Nested fractions, summations, matrices",
    },
    # Multi-line derivations
    "derivation": {
        "font_size": 28,
        "max_symbols": 100,
        "description": "Step-by-step derivations, proofs",
    },
}

LATEX_COLORS = {
    # Variable colors for highlighting
    "variable_x": "#7aa2f7",      # Blue for x variables
    "variable_y": "#9ece6a",      # Green for y variables
    "variable_z": "#bb9af7",      # Purple for z variables
    "constant": "#ff9e64",        # Orange for constants
    "operator": "#c0caf5",        # Soft white for operators
    "highlighted": "#f7768e",     # Pink/red for highlighted terms
    "result": "#e0af68",          # Gold for final results
    "bracket": "#89ddff",         # Cyan for brackets
}

LATEX_ANIMATION_SETTINGS = {
    # Animation durations by type
    "write_simple": 1.0,          # Writing simple equation
    "write_complex": 2.0,         # Writing complex equation
    "transform": 1.5,             # TransformMatchingTex duration
    "indicate": 0.8,              # Indicate animation
    "circumscribe": 1.0,          # Circumscribe (draw box around)
    "fadeout": 0.5,               # FadeOut duration
    "wait_between_steps": 0.8,    # Pause between derivation steps
}

LATEX_SPACING = {
    "equation_gap": 0.6,          # Vertical gap between equations
    "step_number_offset": 0.8,    # Horizontal offset for step numbers
    "annotation_offset": 0.5,     # Gap between equation and annotation
    "group_margin": 0.4,          # Margin around equation groups
}

# ─── LaTeX Best Practices (for prompts) ────────────────────────────────────────

LATEX_BEST_PRACTICES = """
LATEX + MANIM BEST PRACTICES:

1. ALWAYS USE RAW STRINGS:
   ✓ MathTex(r"\\frac{a}{b}")
   ✗ MathTex("\\\\frac{a}{b}")

2. FONT SIZE BY COMPLEXITY:
   - Simple (E=mc²): font_size=48
   - Medium (fractions): font_size=40
   - Complex (integrals): font_size=32
   - Derivations: font_size=28

3. ANIMATION SELECTION:
   - New equation: Write(equation)
   - Transform: TransformMatchingTex(eq1, eq2)
   - Highlight: Indicate(term) or Circumscribe(term)
   - Step reveal: successive Write() with self.wait()

4. COLOR CODING (use sparingly):
   - Variables: BLUE (#7aa2f7) or GREEN (#9ece6a)
   - Constants: ORANGE (#ff9e64)
   - Results: GOLD (#e0af68)
   - Use tex_to_color_map for automatic coloring

5. POSITIONING:
   - Single equation: move_to(ORIGIN) or shift(UP * 0.5)
   - Derivation: VGroup().arrange(DOWN, buff=0.6)
   - With explanation: equation UP*1.5, text DOWN*1

6. TRANSFORMMATCHINGTEX TIPS:
   - Use matching substrings for smooth morphs
   - Define tex_to_color_map for consistent colors
   - Add isolate=["=", "+", "-"] for operator handling
"""


def get_latex_font_size(symbol_count: int) -> int:
    """Get recommended font size based on equation complexity."""
    if symbol_count <= LATEX_FONT_SIZES["simple"]["max_symbols"]:
        return LATEX_FONT_SIZES["simple"]["font_size"]
    if symbol_count <= LATEX_FONT_SIZES["medium"]["max_symbols"]:
        return LATEX_FONT_SIZES["medium"]["font_size"]
    if symbol_count <= LATEX_FONT_SIZES["complex"]["max_symbols"]:
        return LATEX_FONT_SIZES["complex"]["font_size"]
    return LATEX_FONT_SIZES["derivation"]["font_size"]


def count_latex_symbols(latex_str: str) -> int:
    """Count significant symbols in a LaTeX string for complexity estimation."""
    # Remove common LaTeX commands to count actual math symbols
    import re
    # Remove command names but keep their content
    cleaned = re.sub(r'\\[a-zA-Z]+', '', latex_str)
    # Remove braces and common punctuation
    cleaned = re.sub(r'[{}\[\]\\]', '', cleaned)
    # Count remaining non-whitespace characters
    return len(re.sub(r'\s', '', cleaned))


def get_latex_complexity_level(latex_str: str) -> str:
    """Determine complexity level of a LaTeX equation."""
    symbol_count = count_latex_symbols(latex_str)

    # Also check for complex structures
    has_fraction = r'\frac' in latex_str or r'\dfrac' in latex_str
    has_integral = r'\int' in latex_str
    has_sum = r'\sum' in latex_str or r'\prod' in latex_str
    has_matrix = r'matrix' in latex_str or r'pmatrix' in latex_str

    complex_structures = sum([has_fraction, has_integral, has_sum, has_matrix])

    if complex_structures >= 2 or symbol_count > 50:
        return "complex"
    elif complex_structures >= 1 or symbol_count > 25:
        return "medium"
    else:
        return "simple"
