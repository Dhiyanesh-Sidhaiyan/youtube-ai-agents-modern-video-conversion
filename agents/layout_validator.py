"""
Layout Validator for Manim Code

Pre-render validation that checks for common layout mistakes that cause
text overlap and misalignment in dynamically generated scenes.
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class LayoutIssue:
    """A detected layout issue in Manim code."""
    category: str      # positioning, spacing, grouping, overflow
    severity: str      # critical, warning, suggestion
    message: str
    fix_suggestion: str = ""


@dataclass
class LayoutValidationResult:
    """Result of layout validation."""
    valid: bool = True
    issues: List[LayoutIssue] = field(default_factory=list)
    layout_score: int = 100  # 0-100

    def get_critical_issues(self) -> List[LayoutIssue]:
        return [i for i in self.issues if i.severity == "critical"]

    def get_warnings(self) -> List[LayoutIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def format_feedback(self) -> str:
        """Format issues as feedback for LLM retry."""
        if not self.issues:
            return ""

        lines = ["LAYOUT ISSUES TO FIX:"]
        for i, issue in enumerate(self.issues, 1):
            prefix = "CRITICAL" if issue.severity == "critical" else "Warning"
            lines.append(f"{i}. [{prefix}] {issue.message}")
            if issue.fix_suggestion:
                lines.append(f"   Fix: {issue.fix_suggestion}")

        return "\n".join(lines)


def validate_layout(code: str) -> LayoutValidationResult:
    """
    Validate Manim code for layout issues before rendering.

    Checks for:
    1. Hardcoded absolute positions
    2. Missing buff parameters
    3. Multiple elements without VGroup
    4. Missing arrange() for lists
    5. Unsafe positioning methods
    6. Potential overflow issues
    """
    issues: List[LayoutIssue] = []

    # 1. Check for hardcoded absolute positions (common LLM mistake)
    hardcoded_patterns = [
        (r'\.move_to\s*\(\s*\[\s*-?\d', "Hardcoded move_to([x, y, z])"),
        (r'\.move_to\s*\(\s*-?\d', "Hardcoded move_to(number)"),
        (r'\.shift\s*\(\s*\[\s*-?\d', "Hardcoded shift([x, y, z])"),
    ]

    for pattern, desc in hardcoded_patterns:
        if re.search(pattern, code):
            issues.append(LayoutIssue(
                category="positioning",
                severity="warning",
                message=f"{desc} found - may cause misalignment",
                fix_suggestion="Use relative positioning: .next_to(other, DOWN, buff=0.3)"
            ))

    # 2. Check for next_to() without buff parameter
    next_to_matches = re.findall(r'\.next_to\s*\([^)]+\)', code)
    for match in next_to_matches:
        if "buff" not in match:
            issues.append(LayoutIssue(
                category="spacing",
                severity="warning",
                message="next_to() without buff parameter may cause overlap",
                fix_suggestion="Add buff parameter: .next_to(obj, DOWN, buff=0.3)"
            ))
            break  # Only warn once

    # 3. Check for multiple Text elements without VGroup
    text_count = len(re.findall(r'Text\s*\(', code))
    vgroup_count = len(re.findall(r'VGroup\s*\(', code))

    if text_count > 4 and vgroup_count == 0:
        issues.append(LayoutIssue(
            category="grouping",
            severity="critical",
            message=f"{text_count} Text elements without VGroup - high risk of overlap",
            fix_suggestion="Group related texts: items = VGroup(t1, t2, t3).arrange(DOWN, aligned_edge=LEFT)"
        ))
    elif text_count > 2 and vgroup_count == 0:
        issues.append(LayoutIssue(
            category="grouping",
            severity="warning",
            message=f"{text_count} Text elements without VGroup",
            fix_suggestion="Consider grouping with VGroup for better layout control"
        ))

    # 4. Check for missing arrange() with multiple elements
    if text_count > 2 and ".arrange(" not in code:
        issues.append(LayoutIssue(
            category="grouping",
            severity="warning",
            message="Multiple elements without arrange() - likely overlap",
            fix_suggestion="Use .arrange(DOWN, aligned_edge=LEFT, buff=0.25) on VGroups"
        ))

    # 5. Check for safe positioning methods
    safe_methods = [".to_edge(", ".next_to(", ".arrange(", ".align_to("]
    has_safe_positioning = any(method in code for method in safe_methods)

    if not has_safe_positioning and text_count > 1:
        issues.append(LayoutIssue(
            category="positioning",
            severity="critical",
            message="No safe positioning methods used - elements will overlap at origin",
            fix_suggestion="Use .to_edge(UP), .next_to(), or .arrange() for positioning"
        ))

    # 6. Check for large font sizes that may cause overflow
    font_size_matches = re.findall(r'font_size\s*=\s*(\d+)', code)
    for size_str in font_size_matches:
        size = int(size_str)
        if size > 52:
            issues.append(LayoutIssue(
                category="overflow",
                severity="warning",
                message=f"font_size={size} is very large - may overflow screen",
                fix_suggestion="Use font_size <= 48, or add .scale(0.8) after"
            ))

    # 7. Check for multiple to_edge() calls on same direction
    to_edge_up = len(re.findall(r'\.to_edge\s*\(\s*UP', code))
    if to_edge_up > 2:
        issues.append(LayoutIssue(
            category="positioning",
            severity="warning",
            message=f"{to_edge_up} elements positioned at to_edge(UP) - will overlap",
            fix_suggestion="Only title should be at to_edge(UP); use .next_to(title, DOWN) for others"
        ))

    # 8. Check for scale_to_fit usage (good practice)
    has_scale_to_fit = ".scale_to_fit" in code or ".scale(" in code
    estimated_content_heavy = text_count > 5

    if estimated_content_heavy and not has_scale_to_fit:
        issues.append(LayoutIssue(
            category="overflow",
            severity="suggestion",
            message="Heavy content scene without scale - consider adding overflow protection",
            fix_suggestion="Add .scale_to_fit_width(12) or .scale(0.9) to main content group"
        ))

    # 9. Check for very long text strings (> 60 chars per line)
    text_strings = re.findall(r'Text\s*\(\s*["\']([^"\']+)["\']', code)
    for text in text_strings:
        if len(text) > 60:
            issues.append(LayoutIssue(
                category="overflow",
                severity="warning",
                message=f"Long text ({len(text)} chars): '{text[:40]}...' may overflow",
                fix_suggestion="Use smaller font_size (20-24) or split into multiple lines"
            ))

    # Calculate layout score
    score = 100
    for issue in issues:
        if issue.severity == "critical":
            score -= 25
        elif issue.severity == "warning":
            score -= 10
        else:  # suggestion
            score -= 3
    score = max(0, score)

    # Valid if no critical issues
    has_critical = any(i.severity == "critical" for i in issues)

    return LayoutValidationResult(
        valid=not has_critical,
        issues=issues,
        layout_score=score,
    )


def auto_fix_layout(code: str, issues: List[LayoutIssue]) -> str:
    """
    Attempt to auto-fix simple layout issues in the code.

    Note: Most layout issues require LLM regeneration, but some simple
    patterns can be fixed automatically.
    """
    fixed = code

    # Add missing buff to next_to calls
    if any("next_to() without buff" in i.message for i in issues):
        # Add buff=0.3 to next_to calls that don't have it
        fixed = re.sub(
            r'\.next_to\s*\(\s*([^,]+)\s*,\s*(UP|DOWN|LEFT|RIGHT)\s*\)',
            r'.next_to(\1, \2, buff=0.3)',
            fixed
        )

    return fixed


def get_layout_suggestions(code: str) -> list[str]:
    """
    Get specific layout improvement suggestions for the code.

    Returns a list of actionable suggestions.
    """
    suggestions = []

    # Check if using VGroup effectively
    if "VGroup" in code and ".arrange(" not in code:
        suggestions.append(
            "VGroup found without arrange() - add .arrange(DOWN, aligned_edge=LEFT, buff=0.25)"
        )

    # Check for proper title positioning
    if "to_edge(UP" not in code and "Text" in code:
        suggestions.append(
            "No title at to_edge(UP) - consider: title.to_edge(UP, buff=0.5)"
        )

    # Check for centered content with shift
    if "move_to(ORIGIN)" in code or "center()" in code:
        suggestions.append(
            "Centered content - add .shift(DOWN * 0.5) to leave room for title"
        )

    # Suggest scale for safety
    text_count = len(re.findall(r'Text\s*\(', code))
    if text_count > 3 and "scale" not in code:
        suggestions.append(
            f"{text_count} Text elements - consider adding .scale(0.9) to main group for safety"
        )

    return suggestions


# ─── LaTeX Quality Validation ────────────────────────────────────────────────


@dataclass
class LaTeXValidationResult:
    """Result of LaTeX-specific validation."""
    score: int = 100  # 0-100
    issues: List[str] = field(default_factory=list)
    equation_count: int = 0
    complexity_level: str = "simple"


def validate_latex_quality(code: str, narration: str = "") -> LaTeXValidationResult:
    """
    Validate LaTeX/math content quality in Manim code.

    Checks for:
    1. Valid LaTeX syntax patterns
    2. Equation complexity vs font size appropriateness
    3. Proper use of MathTex vs Text
    4. Animation appropriateness for math content
    5. Equation-narration alignment
    """
    issues = []
    score = 100

    # Extract all MathTex content
    mathtex_patterns = re.findall(r'MathTex\s*\(\s*r?["\']([^"\']+)["\']', code)
    equation_count = len(mathtex_patterns)

    # 1. Check for valid LaTeX syntax patterns
    invalid_latex_patterns = [
        (r'\\[a-z]+[^a-z{\\]', "Possible incomplete LaTeX command"),
        (r'\{[^}]*$', "Unclosed brace in LaTeX"),
        (r'\\\\\\\\', "Excessive backslash escaping"),
    ]

    for latex in mathtex_patterns:
        for pattern, desc in invalid_latex_patterns:
            if re.search(pattern, latex):
                issues.append(f"LaTeX syntax issue: {desc} in '{latex[:30]}...'")
                score -= 10
                break

    # 2. Check equation complexity vs font size
    font_size_match = re.search(r'MathTex\s*\([^)]*font_size\s*=\s*(\d+)', code)
    if font_size_match:
        font_size = int(font_size_match.group(1))
        for latex in mathtex_patterns:
            complexity = _count_latex_complexity(latex)
            if complexity > 30 and font_size > 40:
                issues.append(
                    f"Complex equation (complexity={complexity}) with large font_size={font_size} may overflow"
                )
                score -= 15

    # 3. Check for proper MathTex usage
    # Text() used for math-like content
    text_patterns = re.findall(r'Text\s*\(\s*["\']([^"\']+)["\']', code)
    for text in text_patterns:
        if re.search(r'[=+\-*/^].*[a-zA-Z]', text) or re.search(r'\\frac|\\sqrt', text):
            issues.append(f"Mathematical content '{text[:20]}...' should use MathTex instead of Text")
            score -= 10

    # 4. Check animation appropriateness
    has_transform_matching = "TransformMatchingTex" in code
    if has_transform_matching and equation_count < 2:
        issues.append("TransformMatchingTex used but fewer than 2 equations found")
        score -= 10

    # 5. Check for missing raw string prefix
    if re.search(r'MathTex\s*\(\s*"[^r]', code):
        # MathTex with regular string (no 'r' prefix) containing backslashes
        if re.search(r'MathTex\s*\(\s*"[^"]*\\\\[^"]*"', code):
            issues.append("MathTex with escaped backslashes - use raw string: MathTex(r'...')")
            score -= 5

    # 6. Check equation-narration alignment (if narration provided)
    if narration and mathtex_patterns:
        math_vars = set(re.findall(r'[a-zA-Z]', ''.join(mathtex_patterns)))
        narration_vars = set(re.findall(r'\b([a-zA-Z])\b', narration.lower()))
        # Check if key math variables are mentioned in narration
        common_vars = math_vars & narration_vars
        if len(common_vars) < len(math_vars) * 0.3 and len(math_vars) > 3:
            issues.append("Equations may not align with narration content")
            score -= 10

    # Determine complexity level
    total_complexity = sum(_count_latex_complexity(eq) for eq in mathtex_patterns)
    if total_complexity > 100:
        complexity_level = "complex"
    elif total_complexity > 40:
        complexity_level = "medium"
    else:
        complexity_level = "simple"

    return LaTeXValidationResult(
        score=max(0, score),
        issues=issues,
        equation_count=equation_count,
        complexity_level=complexity_level
    )


def _count_latex_complexity(latex: str) -> int:
    """
    Count complexity score of a LaTeX equation.

    Higher scores = more complex:
    - Fractions: +5
    - Integrals/Sums: +8
    - Matrices: +10
    - Subscripts/superscripts: +2
    - Greek letters: +1
    - Each symbol: +1
    """
    score = 0

    # Complex structures
    score += latex.count('\\frac') * 5
    score += latex.count('\\dfrac') * 5
    score += latex.count('\\int') * 8
    score += latex.count('\\sum') * 8
    score += latex.count('\\prod') * 8
    score += latex.count('matrix') * 10
    score += latex.count('\\sqrt') * 3

    # Subscripts and superscripts
    score += latex.count('_') * 2
    score += latex.count('^') * 2

    # Greek letters (common ones)
    greek = ['alpha', 'beta', 'gamma', 'delta', 'theta', 'pi', 'sigma', 'omega']
    for g in greek:
        score += latex.lower().count(g)

    # Base character count
    clean = re.sub(r'\\[a-zA-Z]+', '', latex)  # Remove commands
    clean = re.sub(r'[{}\[\]\\]', '', clean)    # Remove braces
    score += len(re.sub(r'\s', '', clean))       # Count remaining chars

    return score


def get_latex_recommendations(code: str) -> List[str]:
    """
    Get recommendations for improving LaTeX usage in Manim code.
    """
    recommendations = []

    mathtex_count = len(re.findall(r'MathTex\s*\(', code))
    text_count = len(re.findall(r'Text\s*\(', code))

    # Recommend color coding for complex equations
    if mathtex_count > 0 and "tex_to_color_map" not in code:
        recommendations.append(
            "Consider using tex_to_color_map for color-coding variables: "
            "MathTex(r'...', tex_to_color_map={'x': BLUE, 'y': GREEN})"
        )

    # Recommend TransformMatchingTex for derivations
    if mathtex_count >= 2 and "TransformMatchingTex" not in code:
        recommendations.append(
            "Multiple equations found - consider TransformMatchingTex for smooth transitions "
            "between equation steps"
        )

    # Recommend SurroundingRectangle for highlighting
    if mathtex_count > 0 and "SurroundingRectangle" not in code and "Circumscribe" not in code:
        recommendations.append(
            "Consider highlighting key equations with SurroundingRectangle or Circumscribe"
        )

    # Recommend scaling for complex content
    if mathtex_count + text_count > 5 and ".scale" not in code:
        recommendations.append(
            "Heavy content - add scaling protection: group.scale_to_fit_width(11)"
        )

    return recommendations
