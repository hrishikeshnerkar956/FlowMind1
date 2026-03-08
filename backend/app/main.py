from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import pickle
import os
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from app.agent.graph import app as agent_app, HAS_GEMINI
from app.core.database import create_db_and_tables, engine, get_session
from app.models.schema import TelemetryLog

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="FlowMind Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

def flowmind_agentic_loop(telemetry_data: dict) -> dict:
    """
    Observe -> Reason (LLM via LangGraph) -> Decide -> Act -> Learn
    """
    truck = telemetry_data.get("truck", {})
    env = telemetry_data.get("environment", {})
    event = telemetry_data.get("event", "Normal")
    
    weather_desc = env.get("weather", "Clear")
    traffic_desc = env.get("traffic", "Low")
    
    w_feat = WEATHER_MAP.get(weather_desc, 0)
    t_feat = TRAFFIC_MAP.get(traffic_desc, 0)
    c_feat = 1 if event == "Warehouse Congestion" else 0
    
    label = 0
    if delay_model:
        label = delay_model.predict([[w_feat, t_feat, c_feat]])[0]
    
    risk_score = (w_feat * 15) + (t_feat * 20) + (c_feat * 50)
    
    if HAS_GEMINI and agent_app:
        # 3. LangGraph Agent Logic
        state = {
            "telemetry": telemetry_data,
            "ml_label": int(label),
            "ml_risk_score": int(risk_score)
        }
        try:
            result = agent_app.invoke(state)
            analysis = result["analysis"]
            return {
                "original_telemetry": telemetry_data,
                "ai_analysis": {
                    "prediction": analysis.prediction,
                    "risk_score": analysis.risk_score,
                    "reasoning": analysis.reasoning,
                    "action_directive": analysis.action_directive,
                    "requires_human_approval": analysis.requires_human_approval
                }
            }
        except Exception as e:
            print(f"Agent Error: {e}")
            # Fall through to mock logic below

    # Fallback to mock logic if Gemini is not configured or failed
    if label == 2 or risk_score > 65:
        delay_prediction = "High Probability of Delay"
    elif label == 1 or risk_score > 35:
        delay_prediction = "Minor Delay Expected"
    else:
        delay_prediction = "On Time Expected"
    
    reasoning = f"[FALLBACK] Observed {weather_desc} weather and {traffic_desc} traffic. "
    reasoning += f"AI Model predicted class {label} (Risk={risk_score})."
    if event == "Warehouse Congestion":
        reasoning += f" Critical event detected: {event} at destination {truck.get('destination')}."

    directive = "Continue on current route."
    requires_human = False
    
    if label == 2 or risk_score > 65:
        directive = f"REROUTE TO ALTERNATE WAREHOUSE. {truck.get('destination')} is heavily congested."
        requires_human = True
    elif label == 1 or risk_score > 35:
        directive = "REDUCE SPEED AND INCREASE FOLLOWING DISTANCE."
        
    response = {
        "original_telemetry": telemetry_data,
        "ai_analysis": {
            "prediction": delay_prediction,
            "risk_score": risk_score,
            "reasoning": reasoning,
            "action_directive": directive,
            "requires_human_approval": requires_human
        }
    }
    
    # 5. Learn (Log to DB)
    with Session(engine) as session:
        log_entry = TelemetryLog(
            truck_id=truck.get('truck_id', 'UNKNOWN'),
            destination=truck.get('destination', 'UNKNOWN'),
            risk_score=risk_score,
            ai_prediction=delay_prediction,
            ai_reasoning=reasoning,
            ai_directive=directive,
            human_approved=False
        )
        session.add(log_entry)
        session.commit()
    
    return response

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    # Receives data from the local python simulator
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            telemetry = json.loads(data)
            
            # Process incoming telemetry through the Agentic Loop
            processed_event = flowmind_agentic_loop(telemetry)
            
            # Broadcast the enhanced data to all frontend clients
            await manager.broadcast(processed_event)
            
    except WebSocketDisconnect:
        print("Simulator disconnected")

@app.websocket("/ws/frontend")
async def websocket_frontend_endpoint(websocket: WebSocket):
    # Streams data to the React Operations Dashboard
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "human_approval":
                truck_id = message.get('truck_id')
                print(f"Human approved action for truck {truck_id}")
                
                # Update DB
                with Session(engine) as session:
                    stmt = select(TelemetryLog).where(TelemetryLog.truck_id == truck_id).order_by(TelemetryLog.id.desc())
                    latest_log = session.exec(stmt).first()
                    if latest_log:
                        latest_log.human_approved = True
                        session.add(latest_log)
                        session.commit()
                        
                # Broadcast the decision back
                await manager.broadcast({
                    "system_update": True,
                    "message": f"Action approved for {truck_id}"
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"message": "FlowMind API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
