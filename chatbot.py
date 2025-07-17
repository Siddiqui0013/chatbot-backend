from typing import TypedDict, List, Dict, Any, cast
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()

class ChatState(TypedDict):
    step: str
    user_message: str
    bot_response: str
    interests: List[str]
    dislikes: List[str]
    lifestyle: Dict[str, str]
    conversation_history: List[Dict[str, str]]
    message_type: str
    is_complete: bool
    session_id: str

api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(api_key=SecretStr(api_key) if api_key else None, model="llama3-8b-8192")

def llm_call(prompt: str) -> str:
    try:
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            return str(result.content)
        return str(result)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def greeting_node(state: ChatState) -> ChatState:
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
    response = llm_call(prompt)
    state["bot_response"] = response
    state["step"] = "interests"
    state["message_type"] = "question"
    state["conversation_history"].append({"role": "assistant", "content": response})
    return state

def extract_interests_node(state: ChatState) -> ChatState:
    extract_prompt = f"""
    Extract a concise list of user interests or hobbies from the following message. Only return a Python list of strings, nothing else.
    Message: "{state['user_message']}"
    Example output: ["reading", "music", "sports"]
    """
    response = llm_call(extract_prompt)
    try:
        interests = eval(response.strip())
        if isinstance(interests, list):
            state["interests"].extend([str(i) for i in interests])
            state["interests"] = list(set(state["interests"]))
    except Exception:
        pass
    if len(state["interests"]) >= 2:
        prompt = f"""
        The user mentioned: "{state['user_message']}"
        Current interests: {state['interests']}
        Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, friendly response that:
        1. Acknowledges their interests
        2. Asks about things they DON'T like or want to avoid
        3. Keep it concise
        """
        state["step"] = "dislikes"
    else:
        prompt = f"""
        The user mentioned: "{state['user_message']}"
        Current interests: {state['interests']}
        Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, friendly response that:
        1. Acknowledges what they shared
        2. Asks for more interests in different areas
        3. Keep it concise
        """
        state["step"] = "interests"
    response = llm_call(prompt)
    state["bot_response"] = response
    state["message_type"] = "question"
    state["conversation_history"].append({"role": "assistant", "content": response})
    return state

def extract_dislikes_node(state: ChatState) -> ChatState:
    extract_prompt = f"""
    Extract a concise list of activities or hobbies the user dislikes or wants to avoid from the following message. Only return a Python list of strings, nothing else.
    Message: "{state['user_message']}"
    Example output: ["sports", "social activities"]
    """
    response = llm_call(extract_prompt)
    try:
        dislikes = eval(response.strip())
        if isinstance(dislikes, list):
            state["dislikes"].extend([str(i) for i in dislikes])
            state["dislikes"] = list(set(state["dislikes"]))
    except Exception:
        pass
    prompt = f"""
    The user mentioned: "{state['user_message']}"
    Dislikes: {state['dislikes']}
    Interests: {state['interests']}
    Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short response that:
    1. Acknowledges their dislikes
    2. Asks about their lifestyle (time, budget, space)
    3. Keep it concise and understanding
    """
    state["step"] = "lifestyle"
    response = llm_call(prompt)
    state["bot_response"] = response
    state["message_type"] = "question"
    state["conversation_history"].append({"role": "assistant", "content": response})
    return state

def extract_lifestyle_node(state: ChatState) -> ChatState:
    extract_prompt = f"""
    Extract the user's lifestyle information (time availability, budget, space) from the following message. Only return a Python dict with keys 'time_availability', 'budget', and 'space' if mentioned. Use short values. Example: {{'time_availability': 'limited', 'budget': 'flexible', 'space': 'ample'}}
    Message: "{state['user_message']}"
    """
    response = llm_call(extract_prompt)
    try:
        lifestyle = eval(response.strip())
        if isinstance(lifestyle, dict):
            state["lifestyle"].update({str(k): str(v) for k, v in lifestyle.items()})
    except Exception:
        pass
    prompt = f"""
    The user mentioned: "{state['user_message']}"
    Lifestyle: {state['lifestyle']}
    Interests: {state['interests']}
    Dislikes: {state['dislikes']}
    Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Now generate 3 short hobby suggestions that:
    1. Match their interests
    2. Avoid their dislikes
    3. Fit their lifestyle
    4. Include why each hobby suits them (1 line each)
    5. Mention how to get started (1 line each)
    Format as a concise, friendly response with clear recommendations.
    """
    state["step"] = "suggestions"
    response = llm_call(prompt)
    state["bot_response"] = response
    state["message_type"] = "suggestion"
    state["conversation_history"].append({"role": "assistant", "content": response})
    return state

def suggestions_node(state: ChatState) -> ChatState:
    user_message = state["user_message"]
    prompt = f"""
    The user's follow-up: "{user_message}"
    Profile: Interests: {state['interests']}, Dislikes: {state['dislikes']}, Lifestyle: {state['lifestyle']}
    Reply as the assistant, speaking directly to the user. Do not describe what you are doing. Do not start your response with a greeting (like 'Hi', 'Hey', 'Hello', etc.). Generate a short, helpful response that:
    1. Addresses their question or concern
    2. Provides more hobby suggestions if asked
    3. Offers practical advice (1-2 lines)
    4. Keep it concise and supportive
    """
    response = llm_call(prompt)
    state["bot_response"] = response
    state["message_type"] = "followup"
    state["is_complete"] = True
    state["conversation_history"].append({"role": "assistant", "content": response})
    return state

graph = StateGraph(ChatState)
graph.add_node("greeting", greeting_node)
graph.add_node("interests", extract_interests_node)
graph.add_node("dislikes", extract_dislikes_node)
graph.add_node("lifestyle", extract_lifestyle_node)
graph.add_node("suggestions", suggestions_node)

graph.add_edge("greeting", "interests")
graph.add_edge("interests", "dislikes")
graph.add_edge("dislikes", "lifestyle")
graph.add_edge("lifestyle", "suggestions")

graph.set_entry_point("greeting")

compiled_graph = graph.compile()

def get_initial_state(session_id: str) -> ChatState:
    return {
        "step": "greeting",
        "user_message": "",
        "bot_response": "",
        "interests": [],
        "dislikes": [],
        "lifestyle": {},
        "conversation_history": [],
        "message_type": "question",
        "is_complete": False,
        "session_id": session_id
    }

def run_graph(user_message: str, session_id: str, prev_state: ChatState | None = None) -> ChatState:
    if prev_state is None:
        state = get_initial_state(session_id)
    else:
        state = prev_state
    state["user_message"] = user_message
    state["conversation_history"].append({"role": "user", "content": user_message})
    step = state["step"]
    node_map = {
        "greeting": greeting_node,
        "interests": extract_interests_node,
        "dislikes": extract_dislikes_node,
        "lifestyle": extract_lifestyle_node,
        "suggestions": suggestions_node
    }
    if step in node_map:
        result = node_map[step](state)
    else:
        result = state
    return cast(ChatState, result)