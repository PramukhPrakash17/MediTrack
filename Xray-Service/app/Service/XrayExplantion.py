import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class XrayExplanation:

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "openai/gpt-oss-120b"

    def generate_response(self, question: str, yolo_result: str) -> str:

        prompt = f"""
You are an AI assistant for medical X-ray pre-screening.

Based only on the following YOLO detection results, generate a concise medical pre-screening explanation.

Doctor's Question:
{question}

YOLO Detection Results:
{yolo_result}

Instructions:
- Write the response as a professional AI pre-screening report for a doctor.
- Begin by stating whether suspicious regions were detected.
- Mention the number of suspicious regions.
- Mention the highest confidence as a percentage (rounded to the nearest whole number).
- Do not provide a definitive diagnosis.
- Do not invent an anatomical location.
- Keep the response to 2–3 short sentences.
- Do not use headings or bullet points.
- End by recommending review by a qualified clinician.
- Do not include any disclaimer such as "This is an AI-assisted result." The disclaimer will be added separately by the application.

Example style:

"The AI pre-screening model identified 6 suspicious regions that may indicate a possible fracture. The highest detection confidence was 73%. These findings should be reviewed and confirmed by a qualified clinician."
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
            max_completion_tokens=500,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("The LLM returned an empty explanation.")

        return content
