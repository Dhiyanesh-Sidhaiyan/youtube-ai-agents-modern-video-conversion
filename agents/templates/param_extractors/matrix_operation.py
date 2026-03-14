"""Parameter extractor for matrix operation template"""
from agents.templates.utils import call_ollama_json

def extract_matrix_operation_params(scene: dict) -> dict:
    """Extract parameters for matrix operation template."""
    prompt = f"""Extract matrix operation parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- matrix_a: 2D array for first matrix (e.g., [[1, 2], [3, 4]])
- matrix_b: 2D array for second matrix (null if not applicable)
- operation: one of "multiply", "add", "determinant", "inverse"
- result_matrix: 2D array for result (if matrix result)
- scalar_result: string for scalar result like determinant (e.g., "-2")

JSON:"""

    params = call_ollama_json(prompt)

    matrix_a = params.get("matrix_a", [[1, 2], [3, 4]])
    matrix_b = params.get("matrix_b", None)
    operation = params.get("operation", "multiply")
    result_matrix = params.get("result_matrix", [[7, 10], [15, 22]])
    scalar_result = params.get("scalar_result", "")

    # Validate operation
    if operation not in ["multiply", "add", "determinant", "inverse"]:
        operation = "multiply"

    # Ensure matrices are valid 2D arrays
    def validate_matrix(m, default):
        if not isinstance(m, list) or not m:
            return default
        if not all(isinstance(row, list) for row in m):
            return default
        return m

    matrix_a = validate_matrix(matrix_a, [[1, 2], [3, 4]])
    matrix_b = validate_matrix(matrix_b, [[5, 6], [7, 8]]) if matrix_b else None
    result_matrix = validate_matrix(result_matrix, [[19, 22], [43, 50]])

    return {
        "matrix_a": repr(matrix_a),
        "matrix_b": repr(matrix_b) if matrix_b else "None",
        "operation": operation,
        "result_matrix": repr(result_matrix),
        "scalar_result": str(scalar_result)[:20]
    }
