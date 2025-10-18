from flask.cli import load_dotenv
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI

import os

load_dotenv()

ai = Genkit(
    plugins=[GoogleAI()],
    model='googleai/gemini-2.5-flash',
    api_key=os.getenv("GOOGLE_API_KEY")
)

