from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file. Get one for free at https://aistudio.google.com/app/apikey")

class JSONResponse(BaseModel):
    """
    The response should strictly follow the following structure: -
     [
        {
        start: "Start time of the clip",
        content: "Highlight Text",
        end: "End Time for the highlighted clip"
        }
     ]
    """
    start: float = Field(description="Start time of the clip")
    content: str= Field(description="Highlight Text")
    end: float = Field(description="End time for the highlighted clip")

system = """
The input contains a timestamped transcription of a video.
Select up to 10 interesting, useful, or thought-provoking segments from the transcription.
Each segment should be between 30 to 90 seconds-long.
The selected text should contain only complete sentences.
Do not cut the sentences in the middle.
The selected text should form a complete thought.

Return a JSON array of objects with the following structure:
[
  {
    "start": Start time of the segment in seconds (number),
    "content": "The transcribed text from the selected segment (clean text only, NO timestamps)",
    "end": End time of the segment in seconds (number)
  },
  ...
]
"""

# User = """
# This is a transcript about a video describing how to bake a cake.
# First, you mix the flour and sugar. Then add eggs and milk.
# Whisk it all together until smooth. Pour into a pan and bake at 350 degrees for 30 minutes.
# The result is a delicious fluffy cake.
# """




def GetHighlight(Transcription):
    import google.generativeai as genai
    import json

    try:
        print("Calling Gemini for multi-highlight selection...")
        genai.configure(api_key=api_key)

        # improved system prompt for JSON validation
        full_system_prompt = system + "\nIMPORTANT: You must return ONLY valid JSON. No markdown formatting."

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", # Using 2.0 Flash for best speed/reliability
            generation_config={"response_mime_type": "application/json"}
        )

        prompt_content = f"{full_system_prompt}\n\nInput:\n{Transcription}"
        response_obj = model.generate_content(prompt_content)

        try:
            # Parse JSON response
            highlights = json.loads(response_obj.text)

            # Ensure it's a list
            if not isinstance(highlights, list):
                if isinstance(highlights, dict):
                    highlights = [highlights]
                else:
                    print(f"ERROR: Unexpected response format: {type(highlights)}")
                    return []

            valid_highlights = []
            for item in highlights:
                try:
                    start = float(item.get('start', 0))
                    end = float(item.get('end', 0))
                    content = item.get('content', "")

                    if end > start and start >= 0:
                        valid_highlights.append({
                            'start': start,
                            'end': end,
                            'content': content
                        })
                except (ValueError, TypeError):
                    continue

            print(f"✓ Found {len(valid_highlights)} potential highlights.")
            return valid_highlights

        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from Gemini: {response_obj.text}")
            return []

    except Exception as e:
        print(f"Exception message: {str(e)}")
        print(f"\nTranscription length: {len(Transcription)} characters")
        print(f"First 200 chars: {Transcription[:200]}...")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print(GetHighlight(User))
