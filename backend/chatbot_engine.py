import os
import google.generativeai as genai
import re

genai.configure(api_key="AIzaSyAT91-wVf3wejsArBsBkt-aKPWczI_HQ50")

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

    if intent == "explain":
        prompt = f"""
Explain this Flask code step-by-step like a teacher.

If a specific function is mentioned, focus on that.

Code:
{context_str}
"""

    elif intent == "general":
        prompt = f"""
You are a friendly AI coding assistant.

If the user greets you → respond naturally.
If unclear → ask for clarification.

User message:
{query}
"""

    elif intent == "debug":
        prompt = f"""
You are a senior backend engineer.

Find bugs, errors, and issues in this code.
Suggest fixes clearly.

Code:
{context_str}
"""

    elif intent == "optimize":
        prompt = f"""
Improve this Flask code using best practices.

Give:
- issues
- improved code
- explanation

Code:
{context_str}
"""

    elif intent == "feature":
        prompt = f"""
Modify this code to add the requested feature.

User Request:
{query}

Code:
{context_str}
"""

    elif intent == "generate":
        prompt = f"""
Generate or modify code based on request.

Request:
{query}

Context:
{context_str}
"""

    elif intent == "validation":
        prompt = f"""
Analyze validation logic in this code.

Explain:
- how validation works
- missing validations
- improvements

Code:
{context_str}
"""

    elif intent == "performance":
        prompt = f"""
Analyze performance issues in this code.

Suggest:
- bottlenecks
- optimizations

Code:
{context_str}
"""

    else:
        prompt = f"""
Answer the user's question clearly.

Question:
{query}

Context:
{context_str}
"""

    try:
        response = model.generate_content(prompt)

        if not response or not response.text:
            return "⚠️ AI could not generate response. Try again."

        return response.text

    except Exception as e:
        return f"❌ AI Error: {str(e)}"