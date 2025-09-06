
import json 
from typing import List

import anthropic
from jinja2 import Environment, FileSystemLoader

from src.python.manual_solver.constraints import Constraint


PROMPT_TEMPLATE_FILENAME = "constraint_parser.py"

class ConstraintParser:
    def __init__(self, api_key: str):
        self.model = anthropic.Anthropic(api_key=api_key)
        self.template_env = Environment(loader=FileSystemLoader('templates'))

    def _construct_prompt(self, hints: List[str]) -> str:
        template = self.template_env.get_template(PROMPT_TEMPLATE_FILENAME)
        return template.render(hints=hints)

    def parse(self, hint: str) -> Constraint:
        return self.parse_all([hint])[0]

    def parse_all(self, hints: List[str]) -> List[Constraint]:
        prompt = self._construct_prompt(hints)
        response = self.model.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        res = json.loads(response.content[0].text)
        if not isinstance(res, list):
            raise ValueError("Response is not a list")

        constraints = []
        for item in res:
            if item["expression"] is None:
                continue
            constraints.append(Constraint.from_string(item["expression"]))
        return constraints