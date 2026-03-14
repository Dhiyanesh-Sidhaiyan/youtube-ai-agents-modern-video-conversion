"""
Pre-render Manim code validator.

Validates generated Manim code BEFORE rendering to catch common errors early
and provide better feedback to the LLM retry loop.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationIssue:
    """Single validation issue."""
    category: str      # syntax, import, class, method, manim_api, best_practice
    severity: str      # critical, warning, info
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of code validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    code_quality_score: int = 100  # 0-100

    def get_critical_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "critical"]

    def get_warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def format_feedback(self) -> str:
        """Format issues as feedback for LLM retry."""
        if not self.issues:
            return ""

        lines = ["FIX THESE ISSUES IN YOUR CODE:"]
        for i, issue in enumerate(self.issues, 1):
            prefix = "CRITICAL" if issue.severity == "critical" else "Warning"
            lines.append(f"{i}. [{prefix}] {issue.message}")
            if issue.suggestion:
                lines.append(f"   Suggestion: {issue.suggestion}")

        return "\n".join(lines)


def validate_manim_code(code: str, scene_id: int) -> ValidationResult:
    """
    Validate Manim code before rendering.

    Args:
        code: The generated Manim Python code
        scene_id: Expected scene ID for class naming

    Returns:
        ValidationResult with issues and quality score
    """
    issues: List[ValidationIssue] = []

    # 1. Syntax check via AST
    syntax_issues = check_syntax(code)
    issues.extend(syntax_issues)

    # 2. Required structure checks
    structure_issues = check_required_structure(code, scene_id)
    issues.extend(structure_issues)

    # 3. Common Manim API mistakes
    api_issues = check_manim_api_mistakes(code)
    issues.extend(api_issues)

    # 4. Best practices
    practice_issues = check_best_practices(code)
    issues.extend(practice_issues)

    # Calculate quality score
    score = 100
    for issue in issues:
        if issue.severity == "critical":
            score -= 25
        elif issue.severity == "warning":
            score -= 10
        else:
            score -= 2
    score = max(0, score)

    # Valid if no critical issues
    has_critical = any(i.severity == "critical" for i in issues)

    return ValidationResult(
        valid=not has_critical,
        issues=issues,
        code_quality_score=score,
    )


def check_syntax(code: str) -> List[ValidationIssue]:
    """Check Python syntax using AST."""
    issues = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(ValidationIssue(
            category="syntax",
            severity="critical",
            message=f"Syntax error at line {e.lineno}: {e.msg}",
            line=e.lineno,
            suggestion="Check for missing colons, parentheses, or indentation errors"
        ))
    return issues


def check_required_structure(code: str, scene_id: int) -> List[ValidationIssue]:
    """Check required Manim scene structure."""
    issues = []

    # Check import
    if "from manim import" not in code and "import manim" not in code:
        issues.append(ValidationIssue(
            category="import",
            severity="critical",
            message="Missing Manim import",
            suggestion="Add 'from manim import *' at the top"
        ))

    # Check class name
    expected_class = f"Scene{scene_id}"
    class_pattern = rf"class\s+{expected_class}\s*\(\s*Scene\s*\)"
    if not re.search(class_pattern, code):
        # Check if there's any Scene class
        if re.search(r"class\s+\w+\s*\(\s*Scene\s*\)", code):
            issues.append(ValidationIssue(
                category="class",
                severity="critical",
                message=f"Class must be named '{expected_class}', not another name",
                suggestion=f"Rename your class to 'class {expected_class}(Scene):'"
            ))
        else:
            issues.append(ValidationIssue(
                category="class",
                severity="critical",
                message="Missing Scene class definition",
                suggestion=f"Add 'class {expected_class}(Scene):' with construct() method"
            ))

    # Check construct method
    if "def construct(self)" not in code:
        issues.append(ValidationIssue(
            category="method",
            severity="critical",
            message="Missing construct() method",
            suggestion="Add 'def construct(self):' inside your Scene class"
        ))

    return issues


def check_manim_api_mistakes(code: str) -> List[ValidationIssue]:
    """
    Check for common Manim API mistakes.
    Based on actual errors from user's logs.
    """
    issues = []

    # 1. camelCase instead of snake_case
    camel_case_params = [
        ("cornerRadius", "corner_radius"),
        ("fillColor", "fill_color"),
        ("fillOpacity", "fill_opacity"),
        ("strokeColor", "stroke_color"),
        ("strokeWidth", "stroke_width"),
        ("fontSize", "font_size"),
        ("fontColor", "font_color"),
        ("lineWidth", "line_width"),
        ("lineColor", "line_color"),
    ]
    for camel, snake in camel_case_params:
        if camel in code:
            issues.append(ValidationIssue(
                category="manim_api",
                severity="critical",
                message=f"Use '{snake}' not '{camel}' (Manim uses snake_case)",
                suggestion=f"Replace '{camel}' with '{snake}'"
            ))

    # 2. Methods that don't exist on Text
    if ".to_center()" in code:
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="Text has no to_center() method",
            suggestion="Use .move_to(ORIGIN) or .center() instead"
        ))

    # 3. Create() only works on VMobjects, not Text
    if re.search(r"Create\s*\(\s*Text\s*\(", code) or re.search(r"Create\s*\(\s*\w*text", code, re.IGNORECASE):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="Create() doesn't work on Text objects",
            suggestion="Use Write() or FadeIn() for Text objects"
        ))

    # 4. DrawBorderThenFill doesn't work on Text
    if re.search(r"DrawBorderThenFill\s*\(\s*Text", code) or re.search(r"DrawBorderThenFill\s*\(\s*\w*text", code, re.IGNORECASE):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="DrawBorderThenFill doesn't work on Text objects",
            suggestion="Use Write() or FadeIn() for Text objects"
        ))

    # 5. LaggedStart with class instead of instances
    if re.search(r"LaggedStart\s*\(\s*FadeIn\s*,", code):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="LaggedStart needs animation instances, not classes",
            suggestion="Use: LaggedStart(*[FadeIn(item) for item in items])"
        ))

    if re.search(r"LaggedStart\s*\(\s*Write\s*,", code):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="LaggedStart needs animation instances, not classes",
            suggestion="Use: LaggedStart(*[Write(item) for item in items])"
        ))

    # 6. AnimationGroup with classes instead of instances
    if re.search(r"AnimationGroup\s*\(\s*(FadeIn|Write|Create)\s*,", code):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="AnimationGroup needs animation instances, not classes",
            suggestion="Wrap each object: AnimationGroup(FadeIn(obj1), FadeIn(obj2))"
        ))

    # 7. Deprecated ShowCreation - CRITICAL because it causes NameError in newer Manim
    if "ShowCreation" in code:
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="ShowCreation is not defined in Manim CE",
            suggestion="Use Create() instead of ShowCreation()"
        ))

    # 8. AnimationGroup.repeat() doesn't exist
    if ".repeat(" in code:
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="AnimationGroup has no 'repeat' method",
            suggestion="Use a loop instead: for _ in range(n): self.play(animation)"
        ))

    # 9. Color broadcasting issues - usually from incorrect color format
    # e.g., using (r, g) instead of (r, g, b) or hex without #
    color_var_pattern = r'color\s*=\s*\(\s*\d+\s*,\s*\d+\s*\)'
    if re.search(color_var_pattern, code):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="Color tuple has only 2 values - needs 3 (RGB) or 4 (RGBA)",
            suggestion="Use color constants (WHITE, BLUE, RED) or hex strings ('#ffffff')"
        ))

    # 8. Using MoveToTarget without set_target
    if "MoveToTarget" in code and ".generate_target()" not in code:
        issues.append(ValidationIssue(
            category="manim_api",
            severity="warning",
            message="MoveToTarget requires generate_target() first",
            suggestion="Call obj.generate_target() before modifying obj.target"
        ))

    # 9. Color as string without proper format
    if re.search(r'color\s*=\s*"#[0-9a-fA-F]+"', code):
        # This is actually fine in newer Manim, but warn about it
        pass  # No issue

    # 10. Using Play with animation class instead of instance
    play_class_pattern = r"self\.play\s*\(\s*(FadeIn|FadeOut|Write|Create|Transform)\s*\)"
    if re.search(play_class_pattern, code):
        issues.append(ValidationIssue(
            category="manim_api",
            severity="critical",
            message="self.play() needs animation instances, not classes",
            suggestion="Use: self.play(FadeIn(object)) not self.play(FadeIn)"
        ))

    return issues


def check_best_practices(code: str) -> List[ValidationIssue]:
    """Check Manim best practices for quality animations."""
    issues = []

    # 1. No wait() at end - animation might end abruptly
    if "self.wait(" not in code and "self.wait()" not in code:
        issues.append(ValidationIssue(
            category="best_practice",
            severity="warning",
            message="No self.wait() found - animation may end abruptly",
            suggestion="Add self.wait(1) or self.wait(2) at the end of construct()"
        ))

    # 2. No background - may have transparency issues
    has_background = (
        "Rectangle" in code and ("fill_color" in code or "fill_opacity" in code) or
        "FullScreenRectangle" in code or
        "self.camera.background_color" in code
    )
    if not has_background:
        issues.append(ValidationIssue(
            category="best_practice",
            severity="info",
            message="No explicit background set",
            suggestion="Add a dark background Rectangle for better visibility"
        ))

    # 3. Text might be too large
    if "Text(" in code and ".scale(" not in code:
        # Check if font_size is reasonable
        font_match = re.search(r"font_size\s*=\s*(\d+)", code)
        if font_match:
            size = int(font_match.group(1))
            if size > 60:
                issues.append(ValidationIssue(
                    category="best_practice",
                    severity="warning",
                    message=f"Large font_size={size} may cause text to overflow",
                    suggestion="Consider using .scale(0.8) or reducing font_size"
                ))

    # 4. Multiple Text objects without VGroup
    text_count = len(re.findall(r"Text\s*\(", code))
    if text_count > 3 and "VGroup" not in code:
        issues.append(ValidationIssue(
            category="best_practice",
            severity="info",
            message=f"Multiple Text objects ({text_count}) without VGroup",
            suggestion="Use VGroup to organize and position multiple text elements"
        ))

    # 5. Hardcoded positions might be off-screen
    hardcoded_positions = re.findall(r"\.\s*move_to\s*\(\s*\[\s*(-?\d+\.?\d*)", code)
    for pos in hardcoded_positions:
        if abs(float(pos)) > 6:
            issues.append(ValidationIssue(
                category="best_practice",
                severity="warning",
                message=f"Position value {pos} may be off-screen (Manim frame is roughly -7 to 7)",
                suggestion="Use relative positioning like .to_edge(UP) or .next_to(other_obj, DOWN)"
            ))

    return issues


def auto_fix_code(code: str, issues: List[ValidationIssue]) -> str:
    """
    Attempt to auto-fix simple issues in the code.
    Returns the fixed code.
    """
    fixed = code

    for issue in issues:
        if issue.category == "manim_api":
            # Fix camelCase to snake_case
            if "Use '" in issue.message and "not '" in issue.message:
                match = re.search(r"Use '(\w+)' not '(\w+)'", issue.message)
                if match:
                    correct, wrong = match.groups()
                    fixed = fixed.replace(wrong, correct)

            # Fix ShowCreation -> Create
            if "ShowCreation" in issue.message:
                fixed = fixed.replace("ShowCreation", "Create")

            # Remove .repeat() calls (they don't exist)
            if "repeat" in issue.message:
                # Remove .repeat(n) calls
                fixed = re.sub(r'\.repeat\s*\(\s*\d+\s*\)', '', fixed)

    # Always apply these fixes regardless of detected issues:
    # 1. ShowCreation -> Create (common LLM mistake)
    if "ShowCreation" in fixed:
        fixed = fixed.replace("ShowCreation", "Create")

    return fixed


# Convenience function for quick validation
def quick_validate(code: str, scene_id: int) -> tuple[bool, str]:
    """
    Quick validation returning (is_valid, feedback_string).
    """
    result = validate_manim_code(code, scene_id)
    return result.valid, result.format_feedback()


def full_validate(code: str, scene_id: int) -> tuple[bool, str, int]:
    """
    Full validation including layout checks.

    Returns:
        Tuple of (is_valid, combined_feedback, quality_score)
    """
    from agents.layout_validator import validate_layout

    # Code validation
    code_result = validate_manim_code(code, scene_id)

    # Layout validation
    layout_result = validate_layout(code)

    # Combine results
    is_valid = code_result.valid and layout_result.valid

    feedback_parts = []
    if code_result.issues:
        feedback_parts.append(code_result.format_feedback())
    if layout_result.issues:
        feedback_parts.append(layout_result.format_feedback())

    combined_feedback = "\n\n".join(feedback_parts) if feedback_parts else ""

    # Combined quality score (average of both)
    quality_score = (code_result.code_quality_score + layout_result.layout_score) // 2

    return is_valid, combined_feedback, quality_score
