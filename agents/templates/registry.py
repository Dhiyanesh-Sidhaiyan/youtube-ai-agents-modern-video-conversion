"""Template registry and scene code generation dispatcher"""
from agents.templates.utils import log_extraction_warning
from agents.templates.template_strings import SCENE_TEMPLATES
from agents.templates.param_extractors import PARAM_EXTRACTORS, extract_concept_params


def generate_scene_code(scene: dict) -> str:
    """
    Generate Manim code from scene data using templates.
    Extracts parameters from visual_description using LLM.
    """
    scene_type = scene.get("scene_type", "concept")
    scene_id = scene["scene_id"]
    title = scene["title"]

    # Get template
    template = SCENE_TEMPLATES.get(scene_type, SCENE_TEMPLATES["concept"])

    # Extract parameters
    extractor = PARAM_EXTRACTORS.get(scene_type, extract_concept_params)
    params = extractor(scene)

    # Add common params
    params["scene_id"] = scene_id
    params["title"] = title[:45]  # Limit title length

    # Fill template
    try:
        code = template.format(**params)
        return code
    except KeyError as e:
        print(f"  Template error: missing param {e}")
        return None
