from typing import Dict, List, Any
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class ConversationState:
    def __init__(self):
        self.current_step = "greeting"
        self.user_interests = []
        self.user_dislikes = []
        self.lifestyle_info = {}
        self.suggested_hobbies = []
        self.conversation_history = []
        self.clarification_needed = False
        self.user_message = ""
        self.bot_response = ""
        self.session_id = ""
        self.message_type = "question"
        self.is_complete = False

class HobbyChatbot:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.sessions = {}
    
    def _generate_response(self, prompt: str) -> str:
        try:
            if not os.getenv("GROQ_API_KEY"):
                return "❌ Error: GROQ_API_KEY not found in environment variables. Please set your API key."
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=1000
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            print(f"Error generating response: {e}")
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                return "❌ Error: Invalid API key. Please check your GROQ_API_KEY."
            return f"❌ Error: {str(e)}"
    
    def _extract_interests(self, message: str) -> List[str]:
        prompt = f"""
        Extract a concise list of user interests or hobbies from the following message. Only return a Python list of strings, nothing else.
        Message: "{message}"
        Example output: ["reading", "music", "sports"]
        """
        response = self._generate_response(prompt)
        try:
            interests = eval(response.strip())
            if isinstance(interests, list):
                return [str(i) for i in interests]
        except Exception:
            pass
        return []

    def _extract_dislikes(self, message: str) -> List[str]:
        prompt = f"""
        Extract a concise list of activities or hobbies the user dislikes or wants to avoid from the following message. Only return a Python list of strings, nothing else.
        Message: "{message}"
        Example output: ["sports", "social activities"]
        """
        response = self._generate_response(prompt)
        try:
            dislikes = eval(response.strip())
            if isinstance(dislikes, list):
                return [str(i) for i in dislikes]
        except Exception:
            pass
        return []

    def _extract_lifestyle_info(self, message: str) -> Dict[str, str]:
        prompt = f"""
        Extract the user's lifestyle information (time availability, budget, space) from the following message. Only return a Python dict with keys 'time_availability', 'budget', and 'space' if mentioned. Use short values. Example: {{'time_availability': 'limited', 'budget': 'flexible', 'space': 'ample'}}
        Message: "{message}"
        """
        response = self._generate_response(prompt)
        try:
            lifestyle = eval(response.strip())
            if isinstance(lifestyle, dict):
                return {str(k): str(v) for k, v in lifestyle.items()}
        except Exception:
            pass
        return {}

    def _handle_greeting(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_message = state.get("user_message", "").lower()
        prompt = f"""
        The user just said: "{state['user_message']}"
        You are a friendly hobby discovery assistant. Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Generate a short, warm greeting that:
        1. Responds to their message
        2. Introduces yourself as a hobby discovery assistant
        3. Explains you'll help them find hobbies that match their interests and lifestyle
        4. Asks them to share what activities they enjoy or are curious about
        5. Give 2-3 examples (e.g. creative, physical, learning, social)
        6. Keep it very concise and encouraging
        """
        response = self._generate_response(prompt)
        state["bot_response"] = response
        state["current_step"] = "collect_interests"
        state["message_type"] = "question"
        return state

    def _handle_collect_interests(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_message = state.get("user_message", "").lower()
        interests = self._extract_interests(user_message)
        state["user_interests"].extend(interests)
        state["user_interests"] = list(set(state["user_interests"]))
        if len(state["user_interests"]) >= 2:
            prompt = f"""
            The user mentioned: "{state['user_message']}"
            Current interests: {state['user_interests']}
            Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, friendly response that:
            1. Acknowledges their interests
            2. Asks about things they DON'T like or want to avoid
            3. Keep it concise
            """
            state["current_step"] = "collect_dislikes"
        else:
            prompt = f"""
            The user mentioned: "{state['user_message']}"
            Current interests: {state['user_interests']}
            Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, friendly response that:
            1. Acknowledges what they shared
            2. Asks for more interests in different areas
            3. Keep it concise
            """
        response = self._generate_response(prompt)
        state["bot_response"] = response
        return state

    def _handle_collect_dislikes(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_message = state.get("user_message", "").lower()
        dislikes = self._extract_dislikes(user_message)
        state["user_dislikes"].extend(dislikes)
        state["user_dislikes"] = list(set(state["user_dislikes"]))
        prompt = f"""
        The user mentioned: "{state['user_message']}"
        Dislikes: {state['user_dislikes']}
        Interests: {state['user_interests']}
        Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short response that:
        1. Acknowledges their dislikes
        2. Asks about their lifestyle (time, budget, space)
        3. Keep it concise and understanding
        """
        response = self._generate_response(prompt)
        state["bot_response"] = response
        state["current_step"] = "collect_lifestyle"
        return state

    def _handle_collect_lifestyle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_message = state.get("user_message", "").lower()
        lifestyle_info = self._extract_lifestyle_info(user_message)
        state["lifestyle_info"].update(lifestyle_info)
        prompt = f"""
        The user mentioned: "{state['user_message']}"
        Lifestyle: {state['lifestyle_info']}
        Interests: {state['user_interests']}
        Dislikes: {state['user_dislikes']}
        Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Now generate 3 short hobby suggestions that:
        1. Match their interests
        2. Avoid their dislikes
        3. Fit their lifestyle
        4. Include why each hobby suits them (1 line each)
        5. Mention how to get started (1 line each)
        Format as a concise, friendly response with clear recommendations.
        """
        response = self._generate_response(prompt)
        state["bot_response"] = response
        state["current_step"] = "handle_followup"
        state["message_type"] = "suggestion"
        return state

    def _handle_followup(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_message = state.get("user_message", "")
        prompt = f"""
        The user's follow-up: "{user_message}"
        Profile: Interests: {state['user_interests']}, Dislikes: {state['user_dislikes']}, Lifestyle: {state['lifestyle_info']}
        Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, helpful response that:
        1. Addresses their question or concern
        2. Provides more hobby suggestions if asked
        3. Offers practical advice (1-2 lines)
        4. Keep it concise and supportive
        """
        response = self._generate_response(prompt)
        state["bot_response"] = response
        state["message_type"] = "followup"
        state["is_complete"] = True
        return state

    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState().__dict__
        state = self.sessions[session_id]
        state["user_message"] = message
        state["session_id"] = session_id
        state["conversation_history"].append({"role": "user", "content": message})
        current_step = state.get("current_step", "greeting")
        if current_step == "greeting":
            result = self._handle_greeting(state)
        elif current_step == "collect_interests":
            result = self._handle_collect_interests(state)
        elif current_step == "collect_dislikes":
            result = self._handle_collect_dislikes(state)
        elif current_step == "collect_lifestyle":
            result = self._handle_collect_lifestyle(state)
        else:
            result = self._handle_followup(state)
        state["conversation_history"].append({"role": "assistant", "content": result["bot_response"]})
        self.sessions[session_id] = result
        return {
            "response": result["bot_response"],
            "session_id": session_id,
            "message_type": result.get("message_type", "question"),
            "is_complete": result.get("is_complete", False)
        }