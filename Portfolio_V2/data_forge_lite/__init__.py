# data_forge_lite/__init__.py

from .question_generator_module import generate_questions
from .utils.db_secrets import get_db_secret

__all__ = ['generate_questions', 'get_db_secret']