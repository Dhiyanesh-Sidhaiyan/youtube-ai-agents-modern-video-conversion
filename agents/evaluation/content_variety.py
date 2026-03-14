"""
Script-level content variety checking (NotebookLM quality).

Responsibility: Validate that a COMPLETE SCRIPT has diverse, non-generic content.
This is a script-level concern (not per-scene), which is why it lives here
separately from scene_quality.py and self_refine.py.
"""

import re
from collections import Counter


def check_content_variety(scenes: list) -> dict:
    """
    Detect and penalize repetitive patterns in scene content.
    This ensures NotebookLM-quality variety in generated scripts.

    Args:
        scenes: List of scene dicts from script.json

    Returns:
        {
            "variety_score": int (0-100),
            "issues": list of issue descriptions,
            "scene_type_distribution": dict,
            "recommendations": list of suggestions
        }
    """
    issues = []
    recommendations = []
    score = 100

    if not scenes:
        return {"variety_score": 0, "issues": ["No scenes to evaluate"], "recommendations": []}

    # 1. Check scene type distribution - penalize overuse
    scene_types = [s.get("scene_type", "unknown") for s in scenes]
    type_counts = Counter(scene_types)
    scene_count = len(scenes)

    for scene_type, count in type_counts.items():
        usage_ratio = count / scene_count
        if usage_ratio > 0.4:
            issues.append(f"Scene type '{scene_type}' overused: {count}/{scene_count} ({usage_ratio*100:.0f}%)")
            score -= 15
            recommendations.append(f"Replace some '{scene_type}' scenes with: comparison, data_chart, timeline, diagram")

    # 2. Check for generic step patterns
    generic_patterns = [
        r"Step 1[^a-z]", r"Step 2[^a-z]", r"Step 3[^a-z]",
        r"Point 1[^a-z]", r"Point 2[^a-z]", r"Point 3[^a-z]",
        r"Feature A[^a-z]", r"Feature B[^a-z]",
        r"Item 1[^a-z]", r"Item 2[^a-z]",
    ]

    for scene in scenes:
        visual_desc = scene.get("visual_description", "")
        narration = scene.get("narration_text", "")
        combined = f"{visual_desc} {narration}"

        for pattern in generic_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                issues.append(f"Scene {scene.get('scene_id', '?')}: Contains generic '{pattern.replace('[^a-z]', '')}' pattern")
                score -= 20
                recommendations.append(f"Scene {scene.get('scene_id')}: Replace generic steps with specific content from transcript")
                break  # Only penalize once per scene

    # 3. Check for visual variety - detect repeated layouts
    visual_patterns = extract_visual_patterns(scenes)
    pattern_counts = Counter(visual_patterns)

    repeated = [(p, c) for p, c in pattern_counts.items() if c > 2 and p != "unknown"]
    for pattern, count in repeated:
        issues.append(f"Visual pattern '{pattern}' repeated {count} times")
        score -= 10
        recommendations.append(f"Vary '{pattern}' layout: try side-by-side, radial, or timeline instead")

    # 4. Check narration variety - similar sentence structures
    narrations = [s.get("narration_text", "")[:50] for s in scenes]
    similar_starts = Counter([n.split()[0] if n else "" for n in narrations])

    for start, count in similar_starts.items():
        if count > 2 and start and len(start) > 2:
            issues.append(f"Narration often starts with '{start}' ({count} times)")
            score -= 5
            recommendations.append("Vary narration openings: use questions, surprising facts, 'What if...'")

    # 5. Check for analogy presence (NotebookLM quality marker)
    analogy_keywords = ["like", "imagine", "think of", "similar to", "just like", "as if"]
    analogy_count = 0
    for scene in scenes:
        text = f"{scene.get('narration_text', '')} {scene.get('visual_description', '')}".lower()
        if any(kw in text for kw in analogy_keywords):
            analogy_count += 1

    expected_analogies = max(1, len(scenes) // 2)
    if analogy_count < expected_analogies:
        issues.append(f"Low analogy count: {analogy_count} (expected {expected_analogies}+)")
        score -= 10
        recommendations.append("Add analogies: 'Think of X like Y...' for abstract concepts")

    score = max(0, min(100, score))

    return {
        "variety_score": score,
        "issues": issues,
        "scene_type_distribution": dict(type_counts),
        "analogy_count": analogy_count,
        "recommendations": recommendations
    }


def extract_visual_patterns(scenes: list) -> list:
    """
    Extract visual layout patterns from scene descriptions.
    Used to detect repetitive visual approaches.
    """
    patterns = []

    layout_keywords = {
        "side-by-side": ["side by side", "side-by-side", "left and right", "two columns"],
        "flow-diagram": ["flow", "arrows between", "connected steps", "→"],
        "centered-text": ["centered", "center of screen", "middle"],
        "bullet-list": ["bullet", "list of", "points"],
        "comparison-boxes": ["two boxes", "comparison", "vs", "versus"],
        "timeline": ["timeline", "sequence", "chronological"],
        "radial": ["radial", "circular", "around center"],
        "hierarchy": ["hierarchy", "tree", "parent-child"],
        "chart": ["chart", "graph", "bar", "pie", "data"],
    }

    for scene in scenes:
        visual_desc = scene.get("visual_description", "").lower()
        pattern_found = "unknown"

        for pattern_name, keywords in layout_keywords.items():
            if any(kw in visual_desc for kw in keywords):
                pattern_found = pattern_name
                break

        patterns.append(pattern_found)

    return patterns


def validate_script_variety(script: dict) -> dict:
    """
    Validate a complete script for content variety.
    Returns variety check results plus recommendations.

    Args:
        script: Script dict with "scenes" key

    Returns:
        Variety check results with pass/fail status
    """
    scenes = script.get("scenes", [])
    result = check_content_variety(scenes)

    passed = result["variety_score"] >= 70 and len(result["issues"]) <= 3
    result["passed"] = passed
    result["status"] = "PASSED" if passed else "NEEDS_IMPROVEMENT"

    if not passed:
        print(f"\n[Variety Check] Score: {result['variety_score']}/100 - NEEDS IMPROVEMENT")
        for issue in result["issues"][:5]:
            print(f"  ⚠️  {issue}")
        print("\nRecommendations:")
        for rec in result["recommendations"][:3]:
            print(f"  → {rec}")
    else:
        print(f"\n[Variety Check] Score: {result['variety_score']}/100 - PASSED ✓")

    return result
