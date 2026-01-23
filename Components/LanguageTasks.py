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
        end: "End Time for the highlighted clip",
        score: "Engagement score between 1-10",
        reason: "Brief reason why this is engaging"
        }
     ]
    """
    start: float = Field(description="Start time of the clip")
    content: str= Field(description="Highlight Text")
    end: float = Field(description="End time for the highlighted clip")
    score: int = Field(description="Engagement score between 1-10", ge=1, le=10)
    reason: str = Field(description="Brief reason why this is engaging")

system = """
The input contains a timestamped transcription of a video.
Identify the MOST ENGAGING, VIRAL-POTENTIAL segments for YouTube Shorts.

Criteria for High Engagement (Score 8-10):
- Hook: The segment starts with a strong statement, question, or surprising fact.
- Value: Provides a clear, standalone tip, joke, or thought-provoking point.
- Energy: The tone is energetic, emotional, or authoritative.
- Completeness: Forms a perfect "Micro-Story" with a clear beginning and end.

Criteria for Filtering (DO NOT SELECT):
- filler words (um, ah, like, you know).
- repetitive information.
- internal housekeeping (e.g., "like and subscribe" unless it's done ironically/funny).
- sections with low energy or off-topic rambling.

Each segment should be between 30 to 90 seconds-long.
The selected text should contain only complete sentences. Do not cut sentences in the middle.

Return a JSON array of objects with the following structure:
[
  {
    "start": number,
    "content": "string",
    "end": number,
    "score": number (1-10),
    "reason": "string"
  }
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
            model_name="gemini-2.5-flash", 
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
                    score = int(item.get('score', 0))
                    reason = item.get('reason', "")
                    
                    if end > start and start >= 0:
                        valid_highlights.append({
                            'start': start,
                            'end': end,
                            'content': content,
                            'score': score,
                            'reason': reason
                        })
                except (ValueError, TypeError):
                    continue

            # Sort by score descending
            valid_highlights.sort(key=lambda x: x['score'], reverse=True)

            print(f"✓ Found {len(valid_highlights)} potential highlights.")
            return valid_highlights
                
        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from Gemini: {response_obj.text}")
            return []
        
    except Exception as e:
        print(f"ERROR: AI Highlight selection failed: {e}")
        return []

if __name__ == "__main__":
    print(GetHighlight(User))
