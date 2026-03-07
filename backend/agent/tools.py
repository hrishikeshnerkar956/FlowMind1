from langchain_core.tools import tool

@tool
def reroute_shipment(truck_id: str, current_destination: str, reason: str) -> str:
    """Suggests a reroute to an alternate warehouse due to congestion or high risk."""
    return f"Suggested reroute for {truck_id} away from {current_destination}. Reason: {reason}"

@tool
def adjust_speed(truck_id: str, new_speed: int, reason: str) -> str:
    """Suggests an adjusted speed for the truck."""
    return f"Suggested speed change for {truck_id} to {new_speed} mph. Reason: {reason}"

@tool
def escalate_to_human(truck_id: str, risk_score: int, reason: str) -> str:
    """Escalates the decision to a human operator."""
    return f"Escalated {truck_id} to human operator due to risk {risk_score}. Reason: {reason}"

tools = [reroute_shipment, adjust_speed, escalate_to_human]
