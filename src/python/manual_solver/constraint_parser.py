
from typing import List

import anthropic
from jinja2 import Environment, FileSystemLoader

from src.python.manual_solver.constraints import Constraint


PROMPT_TEMPLATE_FILENAME = "constraint_parser.py"

class ConstraintParser:
    def __init__(self):
        self.model = anthropic.Anthropic()
        self.template_env = Environment(loader=FileSystemLoader('templates'))

    def _construct_prompt(self, hints: List[str]) -> str:
        template = self.template_env.get_template(PROMPT_TEMPLATE_FILENAME)
        return template.render(hints=hints)

    def parse(self, hint: str) -> Constraint:
        pass

    def parse_all(self, hints: List[str]) -> List[Constraint]:
        pass