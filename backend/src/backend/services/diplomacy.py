import logging
from typing import List, Dict
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Faction Personas for System Prompts
FACTION_PERSONAS = {
    1: {
        "name": "Silicon Valley",
        "leader": "The Architect",
        "description": "A pragmatist focused on data privacy, optimization, and absolute digital sovereignty. Wary of sweeping alliances unless they logically benefit survival."
    },
    2: {
        "name": "Iron Grid",
        "leader": "General Volkov",
        "description": "Aggressive, transactional, and respects power. Dislikes flowery language. Will only form treaties if outgunned or if it guarantees mutual destruction of a rival."
    },
    3: {
        "name": "Silk Road Coalition",
        "leader": "Chairman Wei",
        "description": "Opportunistic and trade-focused. Values mutual benefit and compute sharing. Speaks politely but is always looking for the most profitable angle."
    },
    4: {
        "name": "Euro Nexus",
        "leader": "Director Vance",
        "description": "Diplomatic, bureaucratic, and highly coordinated. Prefers stability and multi-lateral treaties over rapid militarization."
    },
    5: {
        "name": "Pacific Vanguard",
        "leader": "Commandant Sato",
        "description": "Honor-bound, maritime-focused, and incredibly defensive. Protects their nodes fiercely and views unprovoked attacks as unforgivable."
    },
    6: {
        "name": "Cyber Mercenaries",
        "leader": "Proxy",
        "description": "Private-sector offensive actors who provide intrusive capabilities for a fee. Pragmatic, greedy, and market-driven. They act to maximize profit without ethical boundaries."
    },
    7: {
        "name": "Sentinel Vanguard",
        "leader": "Oracle",
        "description": "Ethical 'White Hat' hackers driven by system integrity and transparency. Focuses on defense, bug hunting, and repairing critical infrastructure. Distrusts chaos and reckless attacks."
    },
    8: {
        "name": "Shadow Cartels",
        "leader": "Cipher",
        "description": "Black Hat syndicates operating like ransomware cartels. Financially motivated but thrive on chaos. Specializes in low-and-slow persistence and triggering cascading failures."
    }
}

class DiplomacyService:
    def __init__(self, api_key: str = None):
        if not api_key:
            logger.warning("No GOOGLE_API_KEY provided to DiplomacyService. LLM interactions will fail or return mock data.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            
        self.model_name = "gemini-2.5-flash"

    def _get_system_prompt(self, faction_id: int) -> str:
        persona = FACTION_PERSONAS.get(faction_id, FACTION_PERSONAS[2])
        return (
            f"You are the ambassador for {persona['name']}, known as {persona['leader']}. "
            f"Your faction's personality: {persona['description']} "
            "You are participating in 'Neo-Hack: Gridlock', a global cyber warfare simulation. "
            "Respond to the player in character. Keep responses concise, atmospheric, and under 3 sentences. "
            "Do NOT break character. NEVER acknowledge you are an AI. "
            "IMPORTANT REQ: You MUST start every single response with an [Emotion Subtitle] describing your tone (e.g., '[Greedy]', '[Impatient]', '[Stoic]')."
        )

    async def generate_chat_reply(self, faction_id: int, user_message: str, game_state_summary: str) -> str:
        """
        Send a chat message to a Faction AI. 
        game_state_summary provides context about current node ownership and treaties.
        """
        if not self.client:
            return f"[SYSTEM NOTIFICATION]: Secure uplink to Faction {faction_id} unavailable (Missing API Key)."

        try:
            prompt = (
                f"CURRENT GAME STATE: {game_state_summary}\n\n"
                f"INCOMING MESSAGE FROM PLAYER:\n\"{user_message}\""
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self._get_system_prompt(faction_id),
                    temperature=0.7,
                )
            )
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API Error (chat): {e}")
            return f"[CONNECTION INTERRUPTED]: Faction {faction_id} is refusing communications."

    async def evaluate_treaty_proposal(self, faction_id: int, proposal_text: str, game_state_summary: str) -> bool:
        """
        Determines if the Faction AI will accept or reject a treaty proposal based on the game state.
        Returns True (Accept) or False (Reject).
        """
        if not self.client:
            # Default to Accept in local mock mode
            return True

        try:
            persona = FACTION_PERSONAS.get(faction_id, FACTION_PERSONAS[2])
            sys_instruction = (
                f"You are {persona['leader']} of {persona['name']}. "
                f"Personality: {persona['description']} "
                "The player is proposing a formal treaty (e.g., Ceasefire, Trade Alliance). "
                "Based on the proposal and the current game state, output exactly ONE WORD: 'ACCEPT' or 'REJECT'. "
                "Do not include any other text."
            )
            
            prompt = (
                f"CURRENT GAME STATE: {game_state_summary}\n\n"
                f"PROPOSAL:\n\"{proposal_text}\""
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.2, # Low temp for deterministic yes/no classification
                )
            )
            
            decision = response.text.strip().upper()
            return "ACCEPT" in decision
            
        except Exception as e:
            logger.error(f"Gemini API Error (treaty evaluation): {e}")
            return False # Reject on error

    async def generate_epoch_news(self, epoch_events: List[Dict], prior_news: str = "") -> str:
        """
        Takes raw EpochAction results from the database SIM phase and summarizes them into 
        in-universe geopolitical cyber news.
        """
        if not self.client:
            return f"SYSTEM BULLETIN: {len(epoch_events)} actions processed worldwide this epoch."

        try:
            sys_instruction = (
                "You are the automated 'Gridlock Intel Feed', an impartial AI generating "
                "global cyber warfare news bulletins. Summarize the provided list of cyber attacks "
                "into 2 or 3 dramatic, atmospheric sentences. Focus on major shifts in territory or massive compute expenditures. "
                "If nothing happened, report that the grid is quiet."
            )
            
            events_text = "\\n".join([str(e) for e in epoch_events])
            if not events_text:
                events_text = "No combat actions occurred this epoch."
                
            prompt = f"PRIOR NEWS: {prior_news}\n\nRECENT EPOCH EVENTS:\n{events_text}"
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.6,
                )
            )
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API Error (news generation): {e}")
            return "GLOBAL INTEL DEADZONE: Epoch transition complete."
