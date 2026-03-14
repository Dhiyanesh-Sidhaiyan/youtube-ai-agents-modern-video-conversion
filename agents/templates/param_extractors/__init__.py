"""Parameter extractor functions for all template types"""
from .intro import extract_intro_params
from .concept import extract_concept_params
from .comparison import extract_comparison_params
from .process import extract_process_params
from .example import extract_example_params
from .conclusion import extract_conclusion_params
from .data_chart import extract_data_chart_params
from .math_formula import extract_math_formula_params
from .equation_derivation import extract_equation_derivation_params
from .graph_visualization import extract_graph_visualization_params
from .geometric_theorem import extract_geometric_theorem_params
from .matrix_operation import extract_matrix_operation_params
from .timeline import extract_timeline_params
from .diagram import extract_diagram_params
from .metrics import extract_metrics_params
from .hierarchy import extract_hierarchy_params
from .visual_explanation import extract_visual_explanation_params
from .info_card import extract_info_card_params
from .decision_tree import extract_decision_tree_params

PARAM_EXTRACTORS = {
    "intro": extract_intro_params,
    "concept": extract_concept_params,
    "comparison": extract_comparison_params,
    "process": extract_process_params,
    "example": extract_example_params,
    "conclusion": extract_conclusion_params,
    "data_chart": extract_data_chart_params,
    "math_formula": extract_math_formula_params,
    "equation_derivation": extract_equation_derivation_params,
    "graph_visualization": extract_graph_visualization_params,
    "geometric_theorem": extract_geometric_theorem_params,
    "matrix_operation": extract_matrix_operation_params,
    "timeline": extract_timeline_params,
    "diagram": extract_diagram_params,
    "metrics": extract_metrics_params,
    "hierarchy": extract_hierarchy_params,
    "visual_explanation": extract_visual_explanation_params,
    "info_card": extract_info_card_params,
    "decision_tree": extract_decision_tree_params,
}
