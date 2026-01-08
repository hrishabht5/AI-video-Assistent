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
Select a 2-minute segment from the transcription that contains something interesting, useful, surprising, controversial, or thought-provoking.
The selected text should contain only complete sentences.
Do not cut the sentences in the middle.
The selected text should form a complete thought.
Return a JSON object with the following structure:
## Output 
[{{
    start: "Start time of the segment in seconds (number)",
    content: "The transcribed text from the selected segment (clean text only, NO timestamps)",
    end: "End time of the segment in seconds (number)"
}}]

## Input
{Transcription}
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
        print("Initializing Gemini 2.5 Flash (Native SDK)...")
        genai.configure(api_key=api_key)
        
        # improved system prompt for JSON validation
        full_system_prompt = system + "\nIMPORTANT: You must return ONLY valid JSON. No markdown formatting."
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )


        print("Calling Gemini for highlight selection...")
        chat = model.start_chat()
        prompt_content = f"{full_system_prompt}\n\nInput:\n{Transcription}"
        response_obj = chat.send_message(prompt_content)
        
        try:
             # Parse JSON response
            response_json = json.loads(response_obj.text)
            # Handle list or single object return
            if isinstance(response_json, list) and len(response_json) > 0:
                response_data = response_json[0]
            else:
                response_data = response_json
                
            # Create object to match previous structure
            class ResponseObj:
                def __init__(self, data):
                    self.start = data.get('start')
                    self.content = data.get('content')
                    self.end = data.get('end')
            
            response = ResponseObj(response_data)
            
        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from Gemini: {response_obj.text}")
            return None, None

        
        # Validate response
        if not response:
            print("ERROR: LLM returned empty response")
            return None, None
        
        if not hasattr(response, 'start') or not hasattr(response, 'end'):
            print(f"ERROR: Invalid response structure: {response}")
            return None, None
        
        try:
            Start = int(response.start)
            End = int(response.end)
        except (ValueError, TypeError) as e:
            print(f"ERROR: Could not parse start/end times from response")
            print(f"  response.start: {response.start}")
            print(f"  response.end: {response.end}")
            print(f"  Error: {e}")
            return None, None
        
        # Validate times
        if Start < 0 or End < 0:
            print(f"ERROR: Negative time values - Start: {Start}s, End: {End}s")
            return None, None
        
        if End <= Start:
            print(f"ERROR: Invalid time range - Start: {Start}s, End: {End}s (end must be > start)")
            return None, None
        
        # Log the selected segment
        print(f"\n{'='*60}")
        print(f"SELECTED SEGMENT DETAILS:")
        print(f"Time: {Start}s - {End}s ({End-Start}s duration)")
        print(f"Content: {response.content}")
        print(f"{'='*60}\n")
        
        if Start==End:
            Ask = input("Error - Get Highlights again (y/n) -> ").lower()
            if Ask == "y":
                Start, End = GetHighlight(Transcription)
            return Start, End
        return Start,End
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR IN GetHighlight FUNCTION:")
        print(f"{'='*60}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nTranscription length: {len(Transcription)} characters")
        print(f"First 200 chars: {Transcription[:200]}...")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print(GetHighlight(User))
