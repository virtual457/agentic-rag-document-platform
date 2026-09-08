from __future__ import annotations

import ast
import operator

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported: {ast.dump(node)}")


class CalcInput(BaseModel):
    expression: str = Field(..., description="Arithmetic expression")


def make_calculator_tool() -> StructuredTool:
    def _calc(expression: str) -> str:
        try:
            return str(_eval(ast.parse(expression, mode="eval").body))
        except Exception as e:
            return f"error: {e}"

    return StructuredTool.from_function(
        func=_calc,
        name="calculator",
        description="Safe arithmetic evaluator: + - * / // % **",
        args_schema=CalcInput,
    )
