import os
from dotenv import load_dotenv
from genkit import ai, configureGenkit
from genkit.plugins import googleai

load_dotenv()

configureGenkit(
    plugins=[googleai.googleai()],
    log_level="debug",
    enable_tracing=False,
)

