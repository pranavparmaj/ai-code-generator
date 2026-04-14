import requests
import re
from rag_engine import retrieve_relevant_snippets

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


# =========================
# STEP 1: INTENT DETECTION
# =========================

def detect_intent_llm(query):
    prompt = f"""
You are an intent classifier for a code assistant.

Classify the user query into EXACTLY one label:

- explain_code → asking to explain code
- debug_code → asking to fix errors/issues
- improve_code → asking to optimize/improve
- generate_feature → asking to add new feature
- general_question → anything else

Examples:

Query: "Why is my login not working?"
Answer: debug_code

Query: "Explain this function"
Answer: explain_code

Query: "Improve performance of this API"
Answer: improve_code

Query: "Add search functionality"
Answer: generate_feature

Query: "What is Flask?"
Answer: general_question

---

Query: {query}

Answer:
"""

    raw_response = call_local_llm(prompt)

    if not raw_response or "⚠️" in raw_response:
        return "general_question"

    response = raw_response.strip().lower()

    valid = {
        "explain_code",
        "debug_code",
        "improve_code",
        "generate_feature",
        "general_question"
    }

    return response if response in valid else "general_question"

# =========================
# STEP 2: FOCUS AREA EXTRACTION
# =========================

def extract_focus_area(query):
    keywords = [
        "login", "route", "api", "validation", "form",
        "database", "model", "auth", "session",
        "dashboard", "crud", "function"
    ]

    found = [k for k in keywords if k in query.lower()]
    return ", ".join(found) if found else "general"


# =========================
# STEP 3: CONTEXT BUILDER
# =========================



def clean_code(code):
    if not code:
        return ""

    # Remove HTML/XML tags
    code = re.sub(r'<[^>]*>', '', code)

    # Remove class="..." patterns
    code = re.sub(r'class="[^"]*"', '', code)

    # Remove leftover class=
    code = re.sub(r'\bclass\s*=\s*', '', code)

    # Remove token artifacts like token-string, token-comment
    code = re.sub(r'token-[a-zA-Z]+', '', code)

    # Remove stray >
    code = code.replace('>', '')

    # Normalize spaces
    code = re.sub(r'\s+', ' ', code)

    return code.strip()


def truncate(text, max_chars=2000):
    if not text:
        return ""
    return text[:max_chars]


def build_context(context, intent, focus_area, query):
    try:
        # =========================
        # 🔥 STEP 1: CLEAN FIRST, THEN TRUNCATE
        # =========================
        raw_code = context.get("backend_code", "")
        cleaned_code = clean_code(raw_code)
        backend_code = truncate(cleaned_code)

        # Debug (IMPORTANT)
        print("FINAL CLEANED CODE:", backend_code[:300])

        # =========================
        # STEP 2: OTHER CONTEXT
        # =========================
        explanation = context.get("explanation", "")
        module = context.get("module", "")
        framework = context.get("framework", "")

        # =========================
        # STEP 3: RAG SNIPPETS
        # =========================
        try:
            snippets = retrieve_relevant_snippets(
                query,
                module=module,
                framework=framework,
                intent=intent,
                entities=[],
                workflows=[]
            )
        except Exception as e:
            print("RAG ERROR:", str(e))
            snippets = []

        # =========================
        # STEP 4: CLEAN SNIPPETS
        # =========================
        snippets_text = ""

        if isinstance(snippets, list):
            cleaned_snippets = []

            for s in snippets[:5]:
                if isinstance(s, str):
                    cleaned_snippets.append(clean_code(s))

                elif isinstance(s, dict):
                    code_part = s.get("code", "")
                    cleaned_snippets.append(clean_code(str(code_part)))

                else:
                    cleaned_snippets.append(clean_code(str(s)))

            snippets_text = "\n".join(cleaned_snippets)

        # =========================
        # STEP 5: RETURN FINAL CONTEXT
        # =========================
        return {
            "backend_code": backend_code,
            "explanation": explanation,
            "module": module,
            "framework": framework,
            "snippets": snippets_text
        }

    except Exception as e:
        print("BUILD CONTEXT ERROR:", str(e))
        return {
            "backend_code": "",
            "explanation": "",
            "module": "",
            "framework": "",
            "snippets": ""
        }

# =========================
# STEP 4: PROMPT BUILDER
# =========================

def construct_prompt(query, context, intent, focus_area):
    return f"""
You are an enterprise-grade AI code assistant.

STRICT RULES:
- Use given context if relevant, otherwise answer generally
- Always try to provide a helpful response
- Do NOT hallucinate
- Be precise and concise
- Focus on developer help

Context:
Module: {context['module']}
Framework: {context['framework']}
Intent: {intent}
Focus Area: {focus_area}

Backend Code:
{context['backend_code']}

Explanation:
{context['explanation']}

Relevant Snippets:
{context['snippets']}

User Question:
{query}

Instructions:
- If explain → simplify clearly
- If debug → find issues and fixes
- If improve → suggest better patterns
- If feature → give implementation steps

Answer:
"""


# =========================
# STEP 5: LOCAL LLM CALL
# =========================

def call_local_llm(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
      # ADD THIS LINE
        print("OLLAMA STATUS:", response.status_code, "RESPONSE:", response.text[:300])

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("response")

    except requests.exceptions.ConnectionError:
        return "⚠️ Local AI model not available. Please start Ollama."

    except Exception:
        return "⚠️ Unable to process request."
    



# =========================
# STEP 6: MAIN PIPELINE
# =========================

def generate_reply(query, context):
    try:
        # 1. Intent detection
        intent = detect_intent_llm(query)

        # 2. Focus extraction
        focus_area = extract_focus_area(query)

        # 3. Context build
        enriched_context = build_context(context, intent, focus_area, query)

        # 4. Prompt
        prompt = construct_prompt(query, enriched_context, intent, focus_area)

        # 5. LLM call
        response = call_local_llm(prompt)

        # Safety fallback
        if not response or "⚠️" in response or "❌" in response:
            return "⚠️ Ollama is not reachable. Please ensure Ollama is running with: ollama serve"
        
        # Strip prompt echo if model repeats it
        if "Answer:" in response:
            response = response.split("Answer:")[-1].strip()

        return response
        

    except Exception as e:
        print("CHATBOT ERROR:", str(e))
        return "❌ Chatbot system error."