# mymodule/mymodule/__init__.py

from .operations import add, subtract, multiply, divide

__all__ = ["add", "subtract", "multiply", "divide"]

# Optional print to confirm the module is initialized
print("Initializing mymodule package")
