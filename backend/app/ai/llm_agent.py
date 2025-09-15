
import os, json, httpx
from typing import Dict, Any, List
from app.settings import settings

BASE_URL = settings.llm_base_url
MODEL = settings.llm_model
API_KEY = settings.llm_api_key
HEADERS = {"Authorization": f"Bearer {API_KEY}" if API_KEY else "", "Content-Type": "application/json"}
JSON_SCHEMA = {
  "actions": [{"type": "reassign|swap|shift", "flight_id": "integer", "from_crew_id": "integer or null", "to_crew_id": "integer or null"}],
  "kpis": {
    "overtime_delta": "number (positive = increased overtime, negative = reduced overtime)",
    "standby_delta": "number (positive = more standby used, negative = less standby used)",
    "fairness_delta": "number (positive = improved fairness, negative = reduced fairness)",
    "compliance": "boolean (true if all DGCA regulations are met)",
    "cost_impact": "string (low/moderate/high) estimated financial impact"
  },
  "explanation": "string (detailed explanation of the proposed changes and rationale)",
  "confidence": "number (0-100, confidence level in the proposed solution)"
}
SYSTEM_PROMPT = """You are an airline crew rostering assistant. Propose minimal, DGCA-compliant changes that consider crew preferences and fairness.

Optimization objectives (in order of priority):
1. Regulatory compliance (DGCA rules) - MUST NOT be violated
2. Crew safety and fatigue management - MUST be maintained
3. Operational efficiency - minimize disruptions
4. Crew satisfaction - consider preferences and fairness

Crew preferences are weighted as follows:
- Day off requests: weight 10 (high priority)
- Base location preferences: weight 2 (moderate priority)
- Destination preferences: weight 1 (low priority)
- Specific flight preferences: weight 3 (medium priority)
- Weekend off preferences: weight 5 (medium-high priority)

Fairness metrics to consider:
- Equal distribution of duties across crew members
- Balanced consecutive duty days
- Fair distribution of night duties

Output JSON matching this example: {"actions":[],"kpis":{},"explanation":""}"""
ASK_SYSTEM_PROMPT = "You are a helpful airline ops assistant. Answer questions concisely using the provided context. When specific data is available in the context, use it to provide accurate answers. If the context doesn't contain relevant information, provide a general response."
def _chat_completion(messages: List[Dict[str,str]], response_format=None) -> str:
    if not API_KEY:
        raise RuntimeError("LLM_API_KEY not set")
    payload = {"model": MODEL, "messages": messages}
    if response_format == "json_object":
        payload["response_format"] = {"type":"json_object"}
    
    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=60.0) as client:
        try:
            r = client.post("/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 413:
                raise RuntimeError("Request payload too large for LLM API. Please try again with a smaller request.")
            else:
                raise
def suggest_patch(context: Dict[str,Any]) -> Dict[str,Any]:
    # Reduce context size by limiting crew pool to 10 and only sending essential info
    if "crew_pool" in context and len(context["crew_pool"]) > 10:
        context["crew_pool"] = context["crew_pool"][:10]
    
    # Simplify the prompt
    user_prompt = "Flight: " + json.dumps(context["flight"]) + "\nCrew: " + json.dumps(context["crew_pool"])
    content = _chat_completion([{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user_prompt}], response_format="json_object")
    try:
        return json.loads(content)
    except Exception:
        import re
        m = re.search(r'\{[\s\S]*\}', content)
        if m: return json.loads(m.group(0))
        raise
def ask_freeform(question:str, context:Dict[str,Any]) -> str:
    user_prompt = f"Answer concisely. Question: {question}\nContext: {json.dumps(context)}"
    return _chat_completion([{"role":"system","content":ASK_SYSTEM_PROMPT},{"role":"user","content":user_prompt}])

def capture_feedback(suggestion: Dict[str,Any], feedback: str, rating: int) -> None:
    """
    Capture feedback on AI suggestions to enable learning capabilities.
    In a production system, this would store feedback in a database for analysis.
    """
    # For now, we'll just print the feedback
    # In a real implementation, this would store feedback for model improvement
    print(f"Feedback captured for suggestion: {suggestion}")
    print(f"Feedback: {feedback}")
    print(f"Rating: {rating}/5")
