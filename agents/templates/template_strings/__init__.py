"""Template strings for all scene types"""
from .intro import TEMPLATE as INTRO_TEMPLATE
from .concept import TEMPLATE as CONCEPT_TEMPLATE
from .comparison import TEMPLATE as COMPARISON_TEMPLATE
from .process import TEMPLATE as PROCESS_TEMPLATE
from .example import TEMPLATE as EXAMPLE_TEMPLATE
from .conclusion import TEMPLATE as CONCLUSION_TEMPLATE
from .data_chart import TEMPLATE as DATA_CHART_TEMPLATE
from .math_formula import TEMPLATE as MATH_FORMULA_TEMPLATE
from .equation_derivation import TEMPLATE as EQUATION_DERIVATION_TEMPLATE
from .graph_visualization import TEMPLATE as GRAPH_VISUALIZATION_TEMPLATE
from .geometric_theorem import TEMPLATE as GEOMETRIC_THEOREM_TEMPLATE
from .matrix_operation import TEMPLATE as MATRIX_OPERATION_TEMPLATE
from .timeline import TEMPLATE as TIMELINE_TEMPLATE
from .diagram import TEMPLATE as DIAGRAM_TEMPLATE
from .metrics import TEMPLATE as METRICS_TEMPLATE
from .hierarchy import TEMPLATE as HIERARCHY_TEMPLATE
from .visual_explanation import TEMPLATE as VISUAL_EXPLANATION_TEMPLATE
from .info_card import TEMPLATE as INFO_CARD_TEMPLATE
from .decision_tree import TEMPLATE as DECISION_TREE_TEMPLATE

SCENE_TEMPLATES = {
    "intro": INTRO_TEMPLATE,
    "concept": CONCEPT_TEMPLATE,
    "comparison": COMPARISON_TEMPLATE,
    "process": PROCESS_TEMPLATE,
    "example": EXAMPLE_TEMPLATE,
    "conclusion": CONCLUSION_TEMPLATE,
    "data_chart": DATA_CHART_TEMPLATE,
    "math_formula": MATH_FORMULA_TEMPLATE,
    "equation_derivation": EQUATION_DERIVATION_TEMPLATE,
    "graph_visualization": GRAPH_VISUALIZATION_TEMPLATE,
    "geometric_theorem": GEOMETRIC_THEOREM_TEMPLATE,
    "matrix_operation": MATRIX_OPERATION_TEMPLATE,
    "timeline": TIMELINE_TEMPLATE,
    "diagram": DIAGRAM_TEMPLATE,
    "metrics": METRICS_TEMPLATE,
    "hierarchy": HIERARCHY_TEMPLATE,
    "visual_explanation": VISUAL_EXPLANATION_TEMPLATE,
    "info_card": INFO_CARD_TEMPLATE,
    "decision_tree": DECISION_TREE_TEMPLATE,
}
