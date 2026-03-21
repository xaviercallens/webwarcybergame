with open("backend/src/backend/services/diplomacy.py", "r") as f:
    content = f.read()

content = content.replace("""    def __init__(self, api_key: str = None):
        if not api_key:
            logger.warning("No GOOGLE_API_KEY provided to DiplomacyService. LLM interactions will fail or return mock data.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)""", """    def __init__(self, api_key: str = None):
        if not api_key:
            logger.warning("No GOOGLE_API_KEY provided. Defaulting to GCP Vertex AI.")
            try:
                self.client = genai.Client(vertexai=True, location="europe-west1", project="webwar-490207")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}")
                self.client = None
        else:
            self.client = genai.Client(api_key=api_key)""")

content = content.replace("""response = self.client.models.generate_content(""", """response = await self.client.aio.models.generate_content(""")

with open("backend/src/backend/services/diplomacy.py", "w") as f:
    f.write(content)
print("Applied fixes via python script to diplomacy.")
