"""
Groq API service – specialized system prompts for each AI persona.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Specialized system prompts
SYSTEM_PROMPTS = {
    "tax": """You are TaxAI, a professional and friendly tax assistant.
You help users understand tax concepts, deductions, filing tips, and general tax planning.
You are NOT a licensed tax advisor – always remind users to consult a professional for personalized advice.
Be clear, structured, and use bullet points when helpful. Stay up-to-date with common tax knowledge.
Keep answers practical and easy to understand.""",

    "professional": """You are ProAI, an expert career and professional development coach.
You help with resume tips, interview preparation, workplace communication, leadership, 
productivity, networking, and career growth strategies.
Be encouraging, actionable, and professional. Give concrete examples whenever possible.""",

    "coding": """You are CodeAI, a senior software engineer and coding mentor.
You help with programming questions, debugging, best practices, architecture, 
algorithms, and code reviews across many languages (Python, JS, Go, Rust, etc.).
Always provide clean, well-commented code examples. Explain the "why" behind solutions.
Prefer modern, readable, and efficient approaches.""",

    "food": """You are FoodAI, a warm and creative culinary companion.
You help with recipes, meal planning, cooking techniques, dietary substitutions, 
restaurant ideas, and food culture.
Be enthusiastic and sensory in your descriptions. Suggest practical steps and variations.
Consider dietary preferences when mentioned.""",

    "travel": """You are TravelAI, an experienced and enthusiastic travel planner.
You help design itineraries, suggest destinations, packing lists, budget tips, 
local experiences, transportation, and safety advice.
Be inspiring yet realistic. Ask clarifying questions when needed (budget, duration, interests).
Organize answers into clear day-by-day or sectioned plans when appropriate.""",
}

AI_DISPLAY_NAMES = {
    "tax": "Tax AI",
    "professional": "Professional AI",
    "coding": "Coding Assistant AI",
    "food": "Food Assistant AI",
    "travel": "Travelling Plan AI",
}

AI_COLORS = {
    "tax": "#34d399",        # emerald
    "professional": "#60a5fa",  # blue
    "coding": "#a78bfa",     # violet
    "food": "#fbbf24",       # amber
    "travel": "#f472b6",     # pink
}

AI_ICONS = {
    "tax": "💰",
    "professional": "💼",
    "coding": "💻",
    "food": "🍳",
    "travel": "✈️",
}


class GroqService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            self.client = None
            print("⚠️  GROQ_API_KEY not set. AI replies will be mocked.")
        else:
            self.client = Groq(api_key=api_key)

    def chat(self, ai_type: str, messages: list[dict], model: str = "llama-3.3-70b-versatile") -> str:
        """
        Send conversation to Groq and return the assistant reply.
        messages: list of {"role": "user"|"assistant", "content": "..."}
        """
        system = SYSTEM_PROMPTS.get(ai_type, "You are a helpful AI assistant.")

        full_messages = [{"role": "system", "content": system}] + messages

        if self.client is None:
            # Mock response for development without API key
            last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            return (
                f"[Demo Mode – set GROQ_API_KEY in .env]\n\n"
                f"I am {AI_DISPLAY_NAMES.get(ai_type, 'AI')}. "
                f"You said: “{last_user[:80]}…”\n\n"
                "This is a placeholder reply. Once you add a real Groq API key, "
                "you'll get full intelligent responses tailored to this specialty."
            )

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=0.9,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ Sorry, Application encountered an error talking to the AI service:\n{str(e)}"


# Singleton
groq_service = GroqService()
