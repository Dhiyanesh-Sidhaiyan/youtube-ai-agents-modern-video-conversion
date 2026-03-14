"""
Scene Wrapper - Aggressive Auto-Layout Safety Layer for Manim Scenes

This module forcibly ensures ALL content stays within screen bounds by:
1. Replacing dangerous positioning code
2. Injecting auto-fit code that ALWAYS runs
3. Adding boundary enforcement after every animation

Based on research:
- Code2Video (arxiv.org/pdf/2510.01174) - Discrete grid system
- Manim auto_zoom and rescale_to_fit methods
"""

import re

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

FRAME_WIDTH = 14.2
FRAME_HEIGHT = 8.0
SAFE_WIDTH = 11.0   # Aggressive: leave margin
SAFE_HEIGHT = 6.0   # Aggressive: leave margin

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-FIT CODE TO INJECT
# ═══════════════════════════════════════════════════════════════════════════════

# This code is injected at the START of construct() - defines helper function
AUTO_FIT_HELPER = '''
        # ═══ AUTO-FIT HELPER (prevents content going off-screen) ═════════════
        def _auto_fit_content(mobjects_to_fit):
            """Force all content to fit within safe screen bounds."""
            if not mobjects_to_fit:
                return
            try:
                content = VGroup(*[m for m in mobjects_to_fit if hasattr(m, 'get_width')])
                if len(content) == 0:
                    return
                # Get current bounds
                w = content.get_width()
                h = content.get_height()
                # Scale down if too wide
                if w > 11:
                    content.scale(11 / w)
                # Scale down if too tall
                h = content.get_height()  # Recalculate after width scale
                if h > 6:
                    content.scale(6 / h)
                # Check if center is too far from origin
                cx, cy, _ = content.get_center()
                if abs(cx) > 0.5 or abs(cy) > 0.3:
                    # Shift towards center
                    content.move_to(ORIGIN + DOWN * 0.2)
            except Exception:
                pass  # Don't crash on edge cases

'''

# This code is injected BEFORE the final self.wait()
FINAL_FIT_CODE = '''
        # ═══ FINAL AUTO-FIT (ensure everything is on screen) ═════════════════
        try:
            _content = [m for m in self.mobjects if hasattr(m, 'get_width') and m.get_width() > 0.1]
            # Exclude background rectangle
            _content = [m for m in _content if not (hasattr(m, 'get_width') and m.get_width() > 15)]
            if _content:
                _all = VGroup(*_content)
                _w, _h = _all.get_width(), _all.get_height()
                if _w > 11.5:
                    _scale = 11.5 / _w
                    for m in _content:
                        m.scale(_scale)
                _h = VGroup(*_content).get_height()
                if _h > 6.5:
                    _scale = 6.5 / _h
                    for m in _content:
                        m.scale(_scale)
        except Exception:
            pass
'''

# More aggressive version - replaces entire construct wrapper
SAFE_CONSTRUCT_WRAPPER = '''
    def construct(self):
        # ═══ SAFE SCENE SETUP ═══════════════════════════════════════════════
        # Background
        _bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(_bg)

        # Auto-fit helper
        def _ensure_fits(mob):
            """Ensure mobject fits in safe area."""
            if mob.get_width() > 11:
                mob.scale_to_fit_width(10.5)
            if mob.get_height() > 6:
                mob.scale_to_fit_height(5.5)
            return mob

        # ═══ ORIGINAL CONTENT (below) ═══════════════════════════════════════
'''

# ═══════════════════════════════════════════════════════════════════════════════
# POSITION FIXING
# ═══════════════════════════════════════════════════════════════════════════════

def fix_extreme_positions(code: str) -> str:
    """
    Aggressively fix any position values that could cause off-screen content.
    """
    modified = code

    # 1. Fix move_to with array coordinates
    def fix_move_to_array(match):
        try:
            x = float(match.group(1))
            y = float(match.group(2))
            # Clamp to safe values
            x = max(-5, min(5, x))
            y = max(-2.5, min(2.8, y))
            return f'.move_to([{x}, {y}, 0])'
        except:
            return match.group(0)

    modified = re.sub(
        r'\.move_to\s*\(\s*\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*,\s*-?\d+\.?\d*\s*\]\s*\)',
        fix_move_to_array,
        modified
    )

    # 2. Fix UP/DOWN/LEFT/RIGHT multipliers that are too large
    def fix_direction_mult(match):
        direction = match.group(1)
        value = float(match.group(2))
        max_vals = {'UP': 2.8, 'DOWN': 2.5, 'LEFT': 5.0, 'RIGHT': 5.0}
        max_val = max_vals.get(direction, 3.0)
        if value > max_val:
            value = max_val
        return f'{direction} * {value}'

    modified = re.sub(
        r'(UP|DOWN|LEFT|RIGHT)\s*\*\s*(\d+\.?\d*)',
        fix_direction_mult,
        modified
    )

    # 3. Fix shift with extreme values
    def fix_shift(match):
        content = match.group(1)
        # Check for large values
        nums = re.findall(r'(\d+\.?\d*)', content)
        for num in nums:
            if float(num) > 4:
                content = content.replace(num, '2.5')
        return f'.shift({content})'

    modified = re.sub(r'\.shift\s*\(([^)]+)\)', fix_shift, modified)

    return modified


def fix_font_sizes(code: str) -> str:
    """Enforce reasonable font sizes."""
    def fix_size(match):
        size = int(match.group(1))
        if size > 44:
            return 'font_size=42'
        if size < 16:
            return 'font_size=18'
        return match.group(0)

    return re.sub(r'font_size\s*=\s*(\d+)', fix_size, code)


def add_scale_after_arrange(code: str) -> str:
    """Add automatic scaling after arrange() calls."""
    # Find variable.arrange(...) patterns
    def add_scale(match):
        var_name = match.group(1)
        arrange_call = match.group(0)
        # Add scale check after arrange
        scale_code = f'''
        if {var_name}.get_width() > 11:
            {var_name}.scale_to_fit_width(10.5)
        if {var_name}.get_height() > 5.5:
            {var_name}.scale_to_fit_height(5)'''
        return arrange_call + scale_code

    modified = re.sub(
        r'(\w+)\.arrange\s*\([^)]+\)(?!\s*\n\s*if)',  # Only if not already followed by if
        add_scale,
        code
    )

    return modified


def inject_auto_fit_code(code: str) -> str:
    """Inject auto-fit helper and final fit code."""
    modified = code

    # Find def construct(self): and add helper after it
    construct_pattern = r'(def construct\s*\(\s*self\s*\)\s*:)'
    if re.search(construct_pattern, modified):
        # Add helper function after construct definition
        modified = re.sub(
            construct_pattern,
            r'\1' + AUTO_FIT_HELPER,
            modified,
            count=1
        )

    # Find the LAST self.wait() and add final fit before it
    # Use a more robust pattern
    wait_pattern = r'([ \t]+)(self\.wait\s*\([^)]*\))\s*$'
    wait_matches = list(re.finditer(wait_pattern, modified, re.MULTILINE))

    if wait_matches:
        last_match = wait_matches[-1]
        insert_pos = last_match.start()
        indent = last_match.group(1)
        # Insert final fit code with proper indentation
        final_code = FINAL_FIT_CODE.replace('        ', indent)
        modified = modified[:insert_pos] + final_code + '\n' + modified[insert_pos:]
    else:
        # No wait found - add at the very end of construct
        # Find the last line of the class
        lines = modified.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].strip().startswith('#'):
                # Insert before last non-empty line
                indent = '        '  # Default 8 spaces
                lines.insert(i, FINAL_FIT_CODE)
                lines.insert(i + 1, f'{indent}self.wait(2)')
                break
        modified = '\n'.join(lines)

    return modified


def ensure_vgroup_scaling(code: str) -> str:
    """Ensure VGroups are scaled to fit."""
    # Add scaling after VGroup creation with arrange
    pattern = r'(\w+)\s*=\s*VGroup\s*\([^)]+\)\s*\n(\s+)\1\.arrange\s*\([^)]+\)'

    def add_vgroup_scale(match):
        original = match.group(0)
        var_name = match.group(1)
        indent = match.group(2)
        return f'''{original}
{indent}if {var_name}.get_width() > 11:
{indent}    {var_name}.scale_to_fit_width(10.5)'''

    return re.sub(pattern, add_vgroup_scale, code)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def process_manim_code(code: str) -> str:
    """
    Full aggressive processing pipeline for LLM-generated Manim code.

    This function applies multiple fixes to ensure content stays on screen:
    1. Fix extreme position values (move_to, shift, direction multipliers)
    2. Fix font sizes (cap at 44)
    3. Add scaling after arrange() calls
    4. Inject auto-fit helper function
    5. Inject final fit code before last wait()
    """
    processed = code

    # Step 1: Fix dangerous positions
    processed = fix_extreme_positions(processed)

    # Step 2: Fix font sizes
    processed = fix_font_sizes(processed)

    # Step 3: Add scaling after arrange calls
    processed = add_scale_after_arrange(processed)

    # Step 4: Ensure VGroup scaling
    processed = ensure_vgroup_scaling(processed)

    # Step 5: Inject auto-fit code
    processed = inject_auto_fit_code(processed)

    return processed


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_positions_in_code(code: str) -> list:
    """Check for potentially dangerous positions in code."""
    issues = []

    # Check for large coordinate values
    coords = re.findall(r'move_to\s*\(\s*\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', code)
    for x, y in coords:
        x, y = float(x), float(y)
        if abs(x) > 5.5 or abs(y) > 3:
            issues.append(f"Dangerous position: move_to([{x}, {y}, ...])")

    # Check for large multipliers
    mults = re.findall(r'(UP|DOWN|LEFT|RIGHT)\s*\*\s*(\d+\.?\d*)', code)
    for direction, value in mults:
        if float(value) > 4:
            issues.append(f"Large multiplier: {direction} * {value}")

    return issues


# Export
__all__ = ['process_manim_code', 'fix_extreme_positions', 'validate_positions_in_code']
