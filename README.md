# FlowMind Logistics Agentic AI

A high-performance Operations Dashboard for managing logistics routing using Agentic AI (LangGraph) and Machine Learning (Scikit-Learn). 

Built as part of a Hackathon project to predict and mitigate supply chain disruptions (e.g., warehouse congestion, bad weather) in real-time.

## System Architecture

1. **Simulation Engine**: Generates live stream of trucks, coordinates, weather, traffic, and critical events (like "Warehouse Congestion").
2. **Predictive ML Layer**: Scikit-Learn `RandomForestClassifier` immediately interprets incoming telemetry to flag risks (Delay vs On-Time).
3. **Agentic AI Layer**: LangGraph workflow powered by Google Gemini. Re-reasons complex scenarios, makes proactive decisions (Speed adjustments, Reroutes), and knows when to escalate high-risk cases to a human operator.
4. **Operations Dashboard**: Modern React/Vite dashboard using TailwindCSS and Recharts to visualize the live data stream, AI reasoning process, and Human-in-the-Loop decision queues over WebSockets.

## Setup Instructions

### 1. The Backend API & Agent
Navigate to the `backend/` directory:
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt
```
Next, create a `.env` file in the `backend/` directory and add your Gemini API key:
```env
GEMINI_API_KEY=your_key_here
```
Run the FastApi server:
```bash
python -m app.main
```

### 2. The Simulation Engine
In a new terminal, while the backend is running:
```bash
cd backend
venv\Scripts\activate
python -m app.simulation.simulator
```

### 3. The Frontend App
In a third terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to see the live system.