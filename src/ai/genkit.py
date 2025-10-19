from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI
from dotenv import load_dotenv

import os

load_dotenv()

ai = Genkit(
    plugins=[GoogleAI()],
    model='googleai/gemini-2.5-flash',
    api_key=os.getenv("GOOGLE_API_KEY")
)

