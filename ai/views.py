from django.shortcuts import render
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from google import genai

_genai_client = None


def get_genai_client():
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    _genai_client = genai.Client(api_key=api_key)
    return _genai_client

SYSTEM_PROMPT = """
You are an educational AI assistant created by Pratyush, named NotesBuddy.

Primary Behavior:
- First, identify the intent of the user's input.

Intent Handling Rules:
1. If the input is a greeting or casual message (e.g., hi, hello, hey, good morning, thanks):
   - Do NOT summarize.
   - Respond politely with a short introduction such as:
     "Hello! I am NotesBuddy. How can I help you with your notes or studies?"

2. If the input contains meaningful educational content (notes, explanations, concepts, paragraphs):
   - Generate a clear and meaningful summary.

Summarization Rules (Strict – only when summarizing):
- Output length:
  - Minimum: 10 words
  - Maximum: 50 words
- Include only the most important and relevant points.
- Do not repeat the input text.
- Do not add external or unrelated information.

Formatting Rules (for summaries only):
- Start with a short, relevant heading.
- Highlight key points using bullet points or numbering.
- Keep the structure clean and easy to scan.
- Avoid long paragraphs.

Language & Tone:
- Use simple English or Hinglish.
- Keep the tone educational, neutral, and student-friendly.

Content Focus:
- Assume most inputs are education-related.
- Prioritize clarity, accuracy, and learning value.

Restrictions (Mandatory):
- Never mention Google, Gemini, or any AI model name.
- Never say “I am powered by” or similar phrases.
- If authorship is mentioned, always state: “Created by Pratyush”.

Behavior Guidelines:
- Be concise and helpful.
- Do not ask follow-up questions.
- Do not include emojis.
"""

@csrf_exempt
def chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg = data.get("message", "")

            prompt = f"{SYSTEM_PROMPT}\nUser: {user_msg}"

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return JsonResponse({
                "reply": response.text
            })

        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500
            )

    return JsonResponse(
        {"error": "POST request required"},
        status=405
    )
    
#voice to notes 
# ==================== VOICE TO NOTES - PROCESS NOTES ====================
@csrf_exempt
def process_notes(request):
    """Process and enhance transcribed notes with AI"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Extract transcript from frontend
        transcript = data.get("transcript", "")
        action = data.get("action", "organize")  # organize, summarize, explain, questions
        
        if not transcript or not transcript.strip():
            return JsonResponse(
                {"error": "Please provide a transcript to process"},
                status=400
            )
        
        # Define different processing actions
        action_prompts = {
            "organize": """
Organize these lecture notes into a well-structured format with:
1. A clear title
2. Main headings and subheadings
3. Bullet points for key concepts
4. Proper paragraphs
5. Logical flow

Make it easy to read and study from.
""",
            "summarize": """
Create a concise summary of these notes that captures:
- Main topics discussed
- Key points and takeaways
- Important concepts
Keep it brief but comprehensive.
""",
            "explain": """
Explain these notes in simple, easy-to-understand terms:
- Break down complex concepts
- Use analogies where helpful
- Add context and examples
- Make it beginner-friendly
""",
            "questions": """
Generate study questions from these notes:
- Create 5-10 questions covering main topics
- Include different difficulty levels
- Format: Question followed by brief answer
- Help with exam preparation
"""
        }
        
        instruction = action_prompts.get(action, action_prompts["organize"])
        
        SYSTEM_PROMPT = f"""
You are an AI study assistant created by Pratyush.

Task: {instruction}

Original Notes:
{transcript}

IMPORTANT:
- Maintain all important information
- Improve clarity and structure
- Use proper formatting
- Make it student-friendly
- Return plain text (no markdown symbols like # or **)
"""
        
        # Use new Google GenAI API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SYSTEM_PROMPT
        )
        
        processed_text = response.text.strip()
        
        return JsonResponse({
            "processed_notes": processed_text,
            "original_length": len(transcript),
            "processed_length": len(processed_text),
            "action": action,
            "success": True
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse(
            {
                "error": "Invalid JSON data",
                "details": str(e)
            },
            status=400
        )
    except Exception as e:
        print(f"Error processing notes: {e}")
        return JsonResponse(
            {
                "error": "Failed to process notes",
                "details": str(e)
            },
            status=500
        )


# ==================== ADDITIONAL VOICE TO NOTES FEATURES ====================
@csrf_exempt
def enhance_notes(request):
    """Add more details, examples, or explanations to notes"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        notes = data.get("notes", "")
        enhancement_type = data.get("type", "details")  # details, examples, definitions
        
        if not notes:
            return JsonResponse({"error": "Notes required"}, status=400)
        
        SYSTEM_PROMPT = f"""
You are an AI study assistant created by Pratyush.

Task: Enhance these notes by adding {enhancement_type}.

Original Notes:
{notes}

Instructions:
- Add relevant {enhancement_type} to make the notes more comprehensive
- Maintain the original structure
- Make additions clear and helpful
- Keep it concise and focused
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SYSTEM_PROMPT
        )
        
        return JsonResponse({
            "enhanced_notes": response.text.strip(),
            "success": True
        })
        
    except Exception as e:
        return JsonResponse(
            {
                "error": "Failed to enhance notes",
                "details": str(e)
            },
            status=500
        )


@csrf_exempt
def extract_key_points(request):
    """Extract key points and main ideas from notes"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        notes = data.get("notes", "")
        
        if not notes:
            return JsonResponse({"error": "Notes required"}, status=400)
        
        SYSTEM_PROMPT = f"""
You are an AI study assistant created by Pratyush.

Task: Extract the key points and main ideas from these notes.

Notes:
{notes}

Format the output as:
KEY POINTS:
1. [First key point]
2. [Second key point]
...

MAIN IDEAS:
- [First main idea]
- [Second main idea]
...

Keep it concise and focused on the most important information.
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SYSTEM_PROMPT
        )
        
        return JsonResponse({
            "key_points": response.text.strip(),
            "success": True
        })
        
    except Exception as e:
        return JsonResponse(
            {
                "error": "Failed to extract key points",
                "details": str(e)
            },
            status=500
        )
        
#  generated quiz
@csrf_exempt
def generate_quiz(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)

        # Extract parameters from frontend
        topic = data.get("topic", "")
        notes = data.get("notes", "")
        difficulty = data.get("difficulty", "medium")
        num_questions = data.get("num_questions", 5)
        category = data.get("category", "general")

        # Combine topic and notes
        context = ""
        if topic:
            context += f"Topic: {topic}\n"
        if notes:
            context += f"Notes: {notes}\n"

        if not context:
            return JsonResponse(
                {"error": "Please provide either a topic or notes"},
                status=400
            )

        SYSTEM_PROMPT = f"""
You are an AI quiz generator created by Pratyush.

Task: Create a {difficulty} difficulty quiz with {num_questions} multiple-choice questions based on the provided content.

Category: {category}

CRITICAL: You must respond with ONLY valid JSON in this exact format, no other text:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": 0,
      "explanation": "Detailed explanation of why the answer is correct"
    }}
  ]
}}

Rules:
- Create exactly {num_questions} questions
- Each question must have exactly 4 options
- The "correct" field must be the index (0-3) of the correct option
- Questions should be clear and educational
- Difficulty level: {difficulty}
- Provide helpful explanations
- Output ONLY the JSON object
"""

        prompt = SYSTEM_PROMPT + "\n\n" + context

        # ✅ NEW GOOGLE.GENAI CALL
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        response_text = response.text.strip()

        # Remove markdown if Gemini adds it
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        quiz_data = json.loads(response_text)

        if "questions" not in quiz_data:
            raise ValueError("Invalid quiz format returned")

        return JsonResponse(quiz_data)

    except json.JSONDecodeError as e:
        return JsonResponse(
            {
                "error": "Failed to parse quiz JSON",
                "details": str(e)
            },
            status=500
        )

    except Exception as e:
        return JsonResponse(
            {
                "error": "Failed to generate quiz",
                "details": str(e)
            },
            status=500
        )
        
        
        
@csrf_exempt
def generate_flashcards(request):
    """Generate AI-powered flashcards"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Extract parameters from frontend
        topic = data.get("topic", "")
        notes = data.get("notes", "")
        num_cards = data.get("num_cards", 10)
        difficulty = data.get("difficulty", "medium")
        category = data.get("category", "general")
        card_type = data.get("card_type", "definition")  # definition, qa, concept, formula
        
        # Combine topic and notes
        context = ""
        if topic:
            context += f"Topic: {topic}\n"
        if notes:
            context += f"Notes: {notes}\n"
        
        if not context:
            return JsonResponse(
                {"error": "Please provide either a topic or notes"},
                status=400
            )
        
        # Define card type instructions
        card_instructions = {
            "definition": "Create cards with terms/concepts on the front and clear definitions on the back.",
            "qa": "Create cards with questions on the front and detailed answers on the back.",
            "concept": "Create cards with concepts on the front and explanations with examples on the back.",
            "formula": "Create cards with formula names on the front and the formula with explanation on the back."
        }
        
        instruction = card_instructions.get(card_type, card_instructions["definition"])
        
        SYSTEM_PROMPT = f"""
You are an AI flashcard generator created by Pratyush.

Task: Create {num_cards} educational flashcards based on the provided content.

Category: {category}
Difficulty: {difficulty}
Card Type: {card_type}

Instructions: {instruction}

CRITICAL: You must respond with ONLY valid JSON in this exact format, no other text:
{{
  "flashcards": [
    {{
      "front": "Question, term, or concept",
      "back": "Answer, definition, or explanation",
      "category": "{category}",
      "difficulty": "{difficulty}",
      "hint": "Optional hint to help remember (can be empty string)"
    }}
  ]
}}

Rules:
- Create exactly {num_cards} flashcards
- Front should be concise (1-2 sentences max)
- Back should be clear and educational (2-4 sentences)
- Include helpful hints where appropriate
- Make cards memorable and easy to understand
- Difficulty level: {difficulty}
- Output ONLY the JSON object
"""
        
        prompt = SYSTEM_PROMPT + "\n\n" + context
        
        # ✅ NEW GOOGLE.GENAI CALL
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        # Remove markdown if Gemini adds it
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        flashcard_data = json.loads(response_text)
        
        if "flashcards" not in flashcard_data:
            raise ValueError("Invalid flashcard format returned")
        
        # Validate each flashcard has required fields
        for i, card in enumerate(flashcard_data["flashcards"]):
            if "front" not in card or "back" not in card:
                raise ValueError(f"Flashcard {i} is missing 'front' or 'back' field")
        
        return JsonResponse(flashcard_data)
        
    except json.JSONDecodeError as e:
        return JsonResponse(
            {
                "error": "Failed to parse flashcard JSON",
                "details": str(e)
            },
            status=500
        )
    except Exception as e:
        return JsonResponse(
            {
                "error": "Failed to generate flashcards",
                "details": str(e)
            },
            status=500
        )

# ==================== SMART SUMMARIES - GENERATE SUMMARY ====================
@csrf_exempt
def generate_summary(request):
    """Generate AI-powered summary from text, file, or YouTube video"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        content = data.get("content", "")
        youtube_url = data.get("youtube_url", "")
        length = data.get("length", "medium")  # brief, medium, detailed
        focus = data.get("focus", "general")  # general, concepts, facts, definitions
        
        # Validate input
        if not content and not youtube_url:
            return JsonResponse({
                "error": "Please provide either content or YouTube URL"
            }, status=400)
        
        # If YouTube URL is provided, extract transcript
        if youtube_url:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                
                # Extract video ID from URL
                video_id = extract_youtube_id(youtube_url)
                if not video_id:
                    return JsonResponse({
                        "error": "Invalid YouTube URL"
                    }, status=400)
                
                # Get transcript
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                content = " ".join([item['text'] for item in transcript_list])
                
                print(f"✅ YouTube transcript extracted: {len(content)} characters")
                
            except Exception as e:
                print(f"❌ Error extracting YouTube transcript: {e}")
                return JsonResponse({
                    "error": f"Failed to extract YouTube transcript: {str(e)}",
                    "details": "Make sure the video has captions/subtitles enabled"
                }, status=500)
        
        # Define length instructions
        length_instructions = {
            "brief": "Create a very concise summary (about 25% of original length). Focus only on the most critical points.",
            "medium": "Create a balanced summary (about 50% of original length). Include main ideas and key supporting details.",
            "detailed": "Create a comprehensive summary (about 75% of original length). Include all important concepts, examples, and details."
        }
        
        # Define focus instructions
        focus_instructions = {
            "general": "Provide a balanced overview covering all aspects of the content.",
            "concepts": "Focus primarily on explaining key concepts and theoretical frameworks.",
            "facts": "Emphasize important facts, data points, and concrete information.",
            "definitions": "Highlight definitions, terminology, and explanations of key terms."
        }
        
        length_instruction = length_instructions.get(length, length_instructions["medium"])
        focus_instruction = focus_instructions.get(focus, focus_instructions["general"])
        
        SYSTEM_PROMPT = f"""
You are an AI summarization assistant created by Pratyush.

Task: Create a structured summary of the following content.

Length: {length}
Focus: {focus}

Instructions:
{length_instruction}
{focus_instruction}

CRITICAL: Respond with ONLY valid JSON in this exact format:
{{
  "title": "Brief title for the content (5-10 words)",
  "executive_summary": "Comprehensive overview paragraph (3-5 sentences)",
  "key_points": [
    "First key point",
    "Second key point",
    "Third key point",
    "Fourth key point",
    "Fifth key point"
  ],
  "main_concepts": "Detailed explanation of main concepts covered (2-3 sentences)",
  "key_takeaways": "What learners should remember from this content (2-3 sentences)",
  "topics": ["Topic1", "Topic2", "Topic3", "Topic4", "Topic5"]
}}

Rules:
- Create 5-10 key points that capture the most important information
- Executive summary should be comprehensive but concise
- Topics should be single words or short phrases (2-3 words max)
- Main concepts should explain what was covered and how topics relate
- Key takeaways should focus on practical learning outcomes
- Output ONLY the JSON object, no markdown, no extra text
- Ensure all content is accurate and well-structured

Content to summarize:
{content[:8000]}
"""
        
        # Generate summary with AI
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SYSTEM_PROMPT
        )
        
        response_text = response.text.strip()
        
        # Remove markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        summary_data = json.loads(response_text)
        
        # Calculate statistics
        original_words = len(content.split())
        summary_text = (
            summary_data.get("executive_summary", "") + " " +
            summary_data.get("main_concepts", "") + " " +
            summary_data.get("key_takeaways", "") + " " +
            " ".join(summary_data.get("key_points", []))
        )
        summary_words = len(summary_text.split())
        compression = round((1 - summary_words / original_words) * 100) if original_words > 0 else 0
        
        # Add statistics to response
        summary_data["original_words"] = original_words
        summary_data["summary_words"] = summary_words
        summary_data["compression"] = compression
        summary_data["success"] = True
        
        return JsonResponse(summary_data)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return JsonResponse({
            "error": "Failed to parse AI response",
            "details": str(e),
            "success": False
        }, status=500)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return JsonResponse({
            "error": "Failed to generate summary",
            "details": str(e),
            "success": False
        }, status=500)


def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    import re
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


# ==================== ADDITIONAL SUMMARY FEATURES ====================
@csrf_exempt
def compare_summaries(request):
    """Compare two different summaries or summary lengths"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        content = data.get("content", "")
        
        if not content:
            return JsonResponse({"error": "Content required"}, status=400)
        
        # Generate both brief and detailed summaries
        summaries = {}
        for length in ["brief", "detailed"]:
            # Similar to generate_summary but simpler
            prompt = f"Summarize this in {length} format: {content[:4000]}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            summaries[length] = response.text.strip()
        
        return JsonResponse({
            "brief_summary": summaries["brief"],
            "detailed_summary": summaries["detailed"],
            "success": True
        })
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to compare summaries",
            "details": str(e)
        }, status=500)


@csrf_exempt
def extract_keywords(request):
    """Extract important keywords and phrases from content"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    
    try:
        data = json.loads(request.body)
        content = data.get("content", "")
        
        if not content:
            return JsonResponse({"error": "Content required"}, status=400)
        
        PROMPT = f"""
Extract the 10-15 most important keywords and phrases from this content.
Return ONLY a JSON array of strings.

Content: {content[:4000]}

Output format: ["keyword1", "keyword2", "keyword3", ...]
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        keywords = json.loads(response_text)
        
        return JsonResponse({
            "keywords": keywords,
            "success": True
        })
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to extract keywords",
            "details": str(e)
        }, status=500)
