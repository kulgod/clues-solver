
import json 
from typing import List

import anthropic
from jinja2 import Environment, FileSystemLoader

from src.python.manual_solver.constraints import Constraint


SYSTEM_PROMPT_FILENAME = "system_prompt.txt"
PROMPT_FILENAME = "hints.txt"

class ConstraintParser:
    def __init__(self, api_key: str):
        self.model = anthropic.Anthropic(api_key=api_key)
        self.template_env = Environment(loader=FileSystemLoader('prompts'))

    def _load_template(self, filename: str, **kwargs) -> str:
        template = self.template_env.get_template(filename)
        return template.render(**kwargs)

    def parse_all(self, hints: List[str]) -> List[Constraint]:
        system_prompt = self._load_template(SYSTEM_PROMPT_FILENAME)
        prompt = self._load_template(PROMPT_FILENAME, hints=hints)

        response = self.model.messages.create(
            model="claude-sonnet-4-20250514",
            system=[
                {"type": "text", "text": system_prompt}
            ],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        res = json.loads(response.content[0].text)
        if not isinstance(res, list):
            raise ValueError("Response is not a list")
        
        constraints = [
            Constraint.from_string(c) 
            for item in res
            for c in item["expressions"]
        ]
        return constraints