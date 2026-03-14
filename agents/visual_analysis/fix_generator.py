"""Fix instruction generation based on visual analysis."""

import json
import os

from .frame_analyzer import SceneVisualAnalysis, VisualIssue, analyze_scene_video


def generate_fix_instructions(analysis: SceneVisualAnalysis, scene_data: dict) -> dict:
    """Generate specific fix instructions based on visual analysis."""
    instructions = {
        "scene_id": analysis.scene_id,
        "needs_fix": analysis.quality_score < 70,
        "current_score": analysis.quality_score,
        "fixes": [],
    }

    # Group issues by type
    issue_types = {}
    for issue in analysis.issues:
        if issue.issue_type not in issue_types:
            issue_types[issue.issue_type] = []
        issue_types[issue.issue_type].append(issue)

    # Generate fixes for each issue type
    if "blank" in issue_types:
        blank_count = len(issue_types["blank"])
        instructions["fixes"].append({
            "type": "animation_content",
            "description": f"Add more animation content - {blank_count} blank frames detected",
            "manim_suggestion": "Add self.wait() calls or extend animations",
        })

    if "offscreen" in issue_types:
        edges = set(i.description.split()[-2] for i in issue_types["offscreen"])
        instructions["fixes"].append({
            "type": "positioning",
            "description": f"Content may be cut off at: {', '.join(edges)}",
            "manim_suggestion": "Use .scale(0.8) or move elements with .shift() away from edges",
        })

    if "contrast" in issue_types:
        instructions["fixes"].append({
            "type": "colors",
            "description": "Improve color contrast",
            "manim_suggestion": "Use WHITE text on dark backgrounds, or BLUE/GREEN on light",
        })

    if "content" in issue_types:
        instructions["fixes"].append({
            "type": "content_density",
            "description": "Low visual content - add more elements",
            "manim_suggestion": "Add Text, shapes, or diagrams to fill the scene",
        })

    # New: Static animation fix
    if "static" in issue_types:
        instructions["fixes"].append({
            "type": "animation",
            "description": "Scene appears static with minimal animation",
            "manim_suggestion": "Add animations: Write(), FadeIn(), GrowFromCenter(), Transform(). Use self.play() for each element.",
        })

    # New: Border cutoff fix
    if "border_cutoff" in issue_types:
        edges = set(i.description.split()[-4] for i in issue_types["border_cutoff"])
        instructions["fixes"].append({
            "type": "border_positioning",
            "description": f"Content appears cut off at borders: {', '.join(edges)}",
            "manim_suggestion": "Use .scale(0.8) on large elements, avoid hardcoded positions > 5, use .to_edge() with buff=0.5",
        })

    # New: Text overlap fix
    if "text_overlap" in issue_types:
        positions = set()
        for issue in issue_types["text_overlap"]:
            # Extract position from description
            desc = issue.description
            if "top" in desc:
                positions.add("top")
            elif "center" in desc:
                positions.add("center")
            elif "bottom" in desc:
                positions.add("bottom")

        instructions["fixes"].append({
            "type": "text_layout",
            "description": f"Text overlap detected in: {', '.join(positions) or 'multiple regions'}",
            "manim_suggestion": (
                "CRITICAL LAYOUT FIX:\n"
                "1. Group text with VGroup: items = VGroup(text1, text2, text3)\n"
                "2. Use arrange: items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)\n"
                "3. Position relative to title: items.next_to(title, DOWN, buff=0.5)\n"
                "4. NEVER use .move_to([x, y, 0]) with hardcoded numbers\n"
                "5. Scale if needed: items.scale_to_fit_width(12)"
            ),
        })

    # Include animation and border info
    instructions["is_animated"] = analysis.is_animated
    instructions["animation_score"] = analysis.animation_score
    instructions["border_issues"] = analysis.border_issues

    return instructions


def analyze_all_scenes(
    scene_results: list,
    scenes_dir: str = "output/scenes",
    output_path: str = "output/visual_analysis.json"
) -> dict:
    """Analyze all scenes and generate a comprehensive report."""
    print("\n[Visual Analyzer] Analyzing animation frames...")

    results = {
        "scenes": [],
        "summary": {
            "total_scenes": len(scene_results),
            "analyzed": 0,
            "avg_quality": 0,
            "needs_improvement": [],
        },
        "fix_instructions": [],
    }

    quality_sum = 0
    analyzed = 0

    for scene in scene_results:
        scene_id = scene["scene_id"]
        mp4_path = scene.get("mp4_path")
        scene_type = scene.get("scene_type", "")

        if mp4_path and os.path.exists(mp4_path):
            print(f"  Scene {scene_id}: Analyzing frames...")
            analysis = analyze_scene_video(mp4_path, scene_id, scene_type=scene_type)
            analyzed += 1
            quality_sum += analysis.quality_score

            results["scenes"].append(analysis.to_dict())

            # Generate fix instructions
            fix_instr = generate_fix_instructions(analysis, scene)
            if fix_instr["needs_fix"]:
                results["fix_instructions"].append(fix_instr)
                results["summary"]["needs_improvement"].append(scene_id)

            status = "✓" if analysis.quality_score >= 70 else "⚠" if analysis.quality_score >= 50 else "✗"
            print(f"    {status} Score: {analysis.quality_score:.0f}/100, Issues: {len(analysis.issues)}")
        else:
            print(f"  Scene {scene_id}: No video file")
            results["scenes"].append({
                "scene_id": scene_id,
                "error": "No video file",
                "quality_score": 0,
            })

    results["summary"]["analyzed"] = analyzed
    results["summary"]["avg_quality"] = quality_sum / max(1, analyzed)

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[Visual Analyzer] Complete:")
    print(f"  Analyzed: {analyzed}/{len(scene_results)} scenes")
    print(f"  Avg Quality: {results['summary']['avg_quality']:.1f}/100")
    print(f"  Need Improvement: {len(results['summary']['needs_improvement'])} scenes")
    print(f"  Report: {output_path}")

    return results
