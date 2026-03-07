import asyncio
import random
import json
import uuid
import datetime
import websockets

# Configuration
NUM_TRUCKS = 10
WAREHOUSES = ["New York", "Chicago", "Los Angeles", "Houston", "Miami"]
WEATHER_CONDITIONS = ["Clear", "Rain", "Snow", "Storm"]
TRAFFIC_LEVELS = ["Low", "Moderate", "Heavy", "Gridlock"]

async def send_telemetry():
    uri = "ws://localhost:8000/ws/telemetry"
    print("Simulator starting... waiting for backend.")
    await asyncio.sleep(2) # Give backend time to start
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to FlowMind Backend Telemetry Stream")
            
            # Initialize trucks
            trucks = []
            for i in range(NUM_TRUCKS):
                trucks.append({
                    "truck_id": f"TRK-{uuid.uuid4().hex[:6].upper()}",
                    "lat": 39.8283 + random.uniform(-5, 5), # Approx US center
                    "lng": -98.5795 + random.uniform(-10, 10),
                    "destination": random.choice(WAREHOUSES),
                    "speed": random.randint(40, 75),
                    "status": "on-time"
                })
            
            while True:
                # Update truck statuses
                for truck in trucks:
                    # Move truck slowly
                    truck["lat"] += random.uniform(-0.05, 0.05)
                    truck["lng"] += random.uniform(-0.05, 0.05)
                    truck["speed"] = max(0, min(80, truck["speed"] + random.randint(-5, 5)))
                    
                    # Generate environment data
                    weather = random.choices(WEATHER_CONDITIONS, weights=[70, 15, 10, 5])[0]
                    traffic = random.choices(TRAFFIC_LEVELS, weights=[50, 30, 15, 5])[0]
                    
                    # Generate a specific event for demo purposes (e.g., Warehouse Congestion)
                    if random.random() < 0.05:
                        event_type = "Warehouse Congestion" 
                    else:
                        event_type = "Normal"

                    payload = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "truck": truck,
                        "environment": {
                            "weather": weather,
                            "traffic": traffic
                        },
                        "event": event_type
                    }
                    
                    await websocket.send(json.dumps(payload))
                
                await asyncio.sleep(1.5) # Send updates periodically
                
    except Exception as e:
        print(f"Simulator Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_telemetry())