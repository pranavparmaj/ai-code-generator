import os
import google.generativeai as genai
import re

genai.configure(api_key="")
#AQ.Ab8RN6Lhc_tzQjEp9y9sTY_5RQymy5QfoXOpbEXNrEWPzK43Fg

model = genai.GenerativeModel("models/gemini-flash-latest")

chat_history = []


def generate_reply(query, context):
    # safety check
    if not query:
        return "⚠️ No query received"

    # 1. understand question type
    intent = detect_intent(query)

    # 2. fetch relevant data
    relevant_context = retrieve_context(intent, context)

    # 3. generate response
    answer = generate_answer(query, relevant_context, intent)

    # store history (optional, not affecting functionality)
    chat_history.append(f"User: {query}")
    chat_history.append(f"Bot: {answer}")

    # final safety
    return answer if answer else "⚠️ Empty response generated"


def detect_intent(query):
    query = query.lower() if query else ""

    if any(word in query for word in [
        "error", "fix", "bug", "issue", "not working",
        "problem", "crash", "exception", "traceback", "fail"
    ]):
        return "debug"

    elif any(word in query for word in [
        "explain", "what is", "how works", "how does",
        "meaning", "describe", "understand", "walkthrough"
    ]):
        return "explain"

    elif any(word in query for word in [
        "improve", "optimize", "enhance", "refactor",
        "better", "clean code", "best practice", "upgrade"
    ]):
        return "optimize"

    elif any(word in query for word in [
        "add", "feature", "implement", "include",
        "create feature", "new feature", "extend", "support"
    ]):
        return "feature"

    elif any(word in query for word in [
        "generate", "write code", "create code",
        "modify", "change", "update code"
    ]):
        return "generate"

    elif any(word in query for word in [
        "validation", "validate", "form error",
        "input check", "field error"
    ]):
        return "validation"

    elif any(word in query for word in [
        "slow", "performance", "speed", "optimize performance"
    ]):
        return "performance"

    return "general"


def retrieve_context(intent, context):
    if not context:
        return "No context provided"

    backend_code = context.get("backend_code", "")
    validation = context.get("validation", "")

    if not backend_code:
        backend_code = "No backend code available"
    if not validation:
        validation = "No validation data available"

    combined_context = f"""
BACKEND CODE:
{backend_code}

VALIDATION:
{validation}
"""

    return combined_context


def clean_code(text):
    if not text:
        return ""

    text = re.sub(r'class="[^"]*">', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\\"', '"')

    return text


def generate_answer(query, context, intent):
    context_str = clean_code(str(context))[:4000]

    # 🔥 COMMON SYSTEM HEADER (VERY IMPORTANT)
    base_prompt = f"""
You are an expert Flask backend developer and AI code assistant.

STRICT RULES:
- You MUST use the provided backend code to answer
- DO NOT say "I don't have the code"
- DO NOT ask the user to provide code
- The code is already given below
- Be precise, helpful, and developer-focused

BACKEND CODE:
{context_str}

USER QUESTION:
{query}

TASK:
"""

    # 🔧 Intent-based instruction
    if intent == "explain":
        prompt = base_prompt + """
Explain the code step-by-step in a simple and clear way.
If a specific function is mentioned, focus on that part.
"""

    elif intent == "general":
        prompt = base_prompt + """
Answer the question clearly using the given code if relevant.
If it is a greeting, respond naturally.
"""

    elif intent == "debug":
        prompt = base_prompt + """
Find bugs, errors, or issues in the code.
Explain the problem and suggest fixes clearly.
"""

    elif intent == "optimize":
        prompt = base_prompt + """
Improve this code using best practices.
Provide:
- issues
- improved approach
- explanation
"""

    elif intent == "feature":
        prompt = base_prompt + """
Explain how to implement the requested feature in this code.
Provide steps and code suggestions.
"""

    elif intent == "generate":
        prompt = base_prompt + """
Generate or modify code based on the user's request using the given context.
"""

    elif intent == "validation":
        prompt = base_prompt + """
Analyze validation logic in the code.
Explain:
- how validation works
- missing validations
- improvements
"""

    elif intent == "performance":
        prompt = base_prompt + """
Analyze performance issues in the code.
Suggest:
- bottlenecks
- optimizations
"""

    else:
        prompt = base_prompt + """
Answer the user's question clearly using the given code.
"""

    try:
        response = model.generate_content(prompt)

        if not response or not response.text:
            return "⚠️ AI could not generate response. Try again."

        return response.text.strip()

    except Exception as e:
        return f"❌ AI Error: {str(e)}"
    
    