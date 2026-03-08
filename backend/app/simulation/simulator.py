import asyncio
import random
import json
import uuid
import datetime
import websockets
import httpx

# Configuration
NUM_TRUCKS = 10
# Major Indian distribution hubs
WAREHOUSES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
WEATHER_CONDITIONS = ["Clear", "Rain", "Snow", "Storm"]
TRAFFIC_LEVELS = ["Low", "Moderate", "Heavy", "Gridlock"]

async def fetch_real_weather(lat: float, lng: float) -> str:
    """Fetch real weather from Open-Meteo and map WMO codes to our ML model's expected string categories."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            
            if resp.status_code == 200:
                data = resp.json()
                wmo_code = data.get("current_weather", {}).get("weathercode", 0)
                
                # Mapping WMO codes to our 4 categories: Clear, Rain, Snow, Storm
                # 0-3: Clear/Cloudy
                # 51-67, 80-82: Rain
                # 71-77, 85-86: Snow
                # 95-99: Thunderstorm/Storm
                if wmo_code in [95, 96, 99]:
                    return "Storm"
                elif wmo_code >= 71 and wmo_code <= 86:
                    return "Snow"
                elif wmo_code >= 51 and wmo_code <= 82:
                    return "Rain"
                else:
                    return "Clear"
    except Exception:
        pass
    
    # Fallback if API fails
    return random.choices(WEATHER_CONDITIONS, weights=[70, 15, 10, 5])[0]

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
                    # Central India approx start points (Nagpur region)
                    "lat": 21.1458 + random.uniform(-5, 5),
                    "lng": 79.0882 + random.uniform(-5, 5),
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
                    
                    # Fetch LIVE weather for Indian coordinate
                    weather = await fetch_real_weather(truck["lat"], truck["lng"])
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