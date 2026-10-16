"""Generate proposals using the evaluated Week 2 prompt file."""
try:
    from .model_service import MODEL, complete, load_prompt
except ImportError:
    from model_service import MODEL, complete, load_prompt

PROMPT_FILE = "prompt-v1.2.txt"


def analyse_requirement(requirement):
    return complete(load_prompt(PROMPT_FILE), requirement, temperature=0.3)["text"]
