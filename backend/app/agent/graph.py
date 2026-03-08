import os
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = bool(os.getenv("GEMINI_API_KEY"))
except ImportError:
    HAS_GEMINI = False

from app.agent.state import AgentState, AIAnalysis

def get_llm():
    if not HAS_GEMINI:
        raise ValueError("GEMINI_API_KEY is missing. Add it to .env or use fallback logic.")
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

def reasoning_node(state: AgentState):
    telemetry = state["telemetry"]
    ml_label = state["ml_label"]
    ml_risk_score = state["ml_risk_score"]
    
    prompt = f"""
    You are an AI logistics agent called FlowMind. Analyze the following telemetry and ML predictions to determine the best course of action.
    
    Telemetry: {telemetry}
    ML Prediction Label (0=On Time, 1=Minor Delay, 2=Major Delay): {ml_label}
    ML Risk Score (0-100): {ml_risk_score}
    
    Based on this, provide a structured analysis. 
    - If the risk score is > 65 or label is 2, require human approval and suggest rerouting (e.g., "REROUTE TO ALTERNATE WAREHOUSE..."). 
    - If risk > 35 or label is 1, suggest speed reduction.
    - Otherwise, continue on current route.
    
    Also include a brief reasoning for your decision based on the observed weather, traffic, and events.
    """
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(AIAnalysis)
    analysis = structured_llm.invoke(prompt)
    
    return {"analysis": analysis}

workflow = StateGraph(AgentState)
workflow.add_node("reason", reasoning_node)
workflow.add_edge(START, "reason")
workflow.add_edge("reason", END)

app = workflow.compile()
