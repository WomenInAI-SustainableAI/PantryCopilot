import os
from dotenv import load_dotenv

load_dotenv()

# Simplified AI interface to replace genkit
class SimpleAI:
    def flow(self):
        def decorator(func):
            return func
        return decorator
    
    async def generate(self, prompt, output_schema=None):
        # Simple mock response for now
        class MockResult:
            def __init__(self):
                if output_schema:
                    self.output = output_schema(explanation="This recipe is recommended based on your inventory and preferences.")
                else:
                    self.output = "This recipe is recommended based on your inventory and preferences."
        return MockResult()

ai = SimpleAI()

