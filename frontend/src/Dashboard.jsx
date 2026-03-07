import { Activity, AlertTriangle, CheckCircle, Clock, MapPin, Truck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const Dashboard = () => {
    const [telemetry, setTelemetry] = useState([]);
    const [trucks, setTrucks] = useState({});
    const [highRiskEvents, setHighRiskEvents] = useState([]);
    const [networkRiskData, setNetworkRiskData] = useState([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // Connect to FastAPI WebSocket
        const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/frontend";
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.system_update) return;

            // Update event log
            setTelemetry(prev => {
                const newLog = [data, ...prev].slice(0, 50); // keep last 50 events
                return newLog;
            });

            // Update fleet status
            const truckData = data.original_telemetry.truck;
            setTrucks(prev => ({
                ...prev,
                [truckData.truck_id]: truckData
            }));

            // Update network risk chart
            const risk = data.ai_analysis.risk_score;
            setNetworkRiskData(prev => {
                const newTime = new Date().toLocaleTimeString();
                const last = prev[prev.length - 1];
                if (last && last.time === newTime) return prev;
                const newData = [...prev, { time: newTime, risk: risk }].slice(-20);
                return newData;
            });

            // Flag high risk events for Human-in-the-Loop
            if (data.ai_analysis.requires_human_approval) {
                setHighRiskEvents(prev => {
                    if (prev.find(e => e.original_telemetry.truck.truck_id === truckData.truck_id)) return prev;
                    return [data, ...prev];
                });
            }
        };

        return () => ws.close();
    }, []);

    const approveEvent = (eventId) => {
        setHighRiskEvents(prev => prev.filter(e => e.original_telemetry.truck.truck_id !== eventId));
    };

    const rejectEvent = (eventId) => {
        setHighRiskEvents(prev => prev.filter(e => e.original_telemetry.truck.truck_id !== eventId));
    };

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 mb-1">FlowMind Logistics</h1>
                    <p className="text-slate-400 text-sm font-medium tracking-wide uppercase">Agentic AI Operations Dashboard</p>
                </div>
                <div className="flex items-center space-x-3 bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700/50">
                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                    <span className="text-slate-300 font-medium text-sm">{isConnected ? 'System Live' : 'Disconnected'}</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Fleet Status Card */}
                <div className="bg-slate-800/40 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-slate-700/50 flex flex-col justify-center">
                    <div className="flex items-center space-x-5">
                        <div className="p-4 bg-blue-500/20 rounded-2xl shadow-inner pointer-events-none">
                            <Truck className="w-10 h-10 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-1">Active Fleet Stream</p>
                            <h2 className="text-4xl font-black text-white">{Object.keys(trucks).length} <span className="text-lg text-slate-500 font-medium">units online</span></h2>
                        </div>
                    </div>
                </div>

                {/* Network Risk Graph */}
                <div className="bg-slate-800/40 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-slate-700/50 lg:col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-slate-200 font-bold flex items-center text-lg"><Activity className="w-5 h-5 mr-3 text-emerald-400" /> Network Risk Telemetry</h3>
                        <div className="text-xs font-semibold px-2 py-1 bg-slate-700/50 rounded-md text-slate-400">Live 20-sec window</div>
                    </div>
                    <div className="h-[180px] w-full">
                        <ResponsiveContainer>
                            <LineChart data={networkRiskData} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickMargin={10} />
                                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} tickCount={5} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' }}
                                    itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                                />
                                <Line type="monotone" dataKey="risk" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981', stroke: '#0f172a', strokeWidth: 2 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-12">
                {/* Human-in-the-Loop Guardrails */}
                <div className="bg-slate-800/40 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-slate-700/50 flex flex-col h-[600px]">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-red-400 font-bold flex items-center text-lg"><AlertTriangle className="w-5 h-5 mr-3" /> Human-in-the-Loop Queue</h3>
                        {highRiskEvents.length > 0 && <span className="bg-red-500/20 text-red-400 px-3 py-1 rounded-full text-xs font-bold ring-1 ring-red-500/50">{highRiskEvents.length} Pending</span>}
                    </div>

                    <div className="space-y-4 overflow-y-auto flex-1 pr-2 custom-scrollbar">
                        {highRiskEvents.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-70">
                                <CheckCircle className="w-16 h-16 text-emerald-500/50 mb-4" />
                                <p className="font-medium text-lg text-emerald-100">Zero High-Risk Events</p>
                                <p className="text-sm">Network operating within safety parameters.</p>
                            </div>
                        ) : (
                            highRiskEvents.map((event, idx) => (
                                <div key={idx} className="bg-slate-900 border border-red-500/30 p-5 rounded-xl shadow-lg relative overflow-hidden group">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
                                    <div className="flex justify-between items-start mb-3">
                                        <h4 className="text-white font-bold text-lg flex items-center bg-slate-800 px-3 py-1 rounded-md"><Truck className="w-4 h-4 mr-2 text-slate-400" /> {event.original_telemetry.truck.truck_id}</h4>
                                        <span className="bg-red-500 text-white text-xs px-3 py-1 rounded-full font-black shadow-md shadow-red-500/20">Risk: {event.ai_analysis.risk_score}</span>
                                    </div>
                                    <div className="bg-slate-800/50 p-3 rounded-lg mb-4 border border-slate-700/50">
                                        <p className="text-slate-300 text-sm leading-relaxed"><strong className="text-slate-400 uppercase text-xs tracking-wider block mb-1">AI Recommendation</strong> {event.ai_analysis.action_directive}</p>
                                    </div>
                                    <div className="flex space-x-3">
                                        <button onClick={() => approveEvent(event.original_telemetry.truck.truck_id)} className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-slate-900 py-2.5 rounded-lg transition-all font-bold shadow-md shadow-emerald-500/20 group-hover:scale-[1.02]">AUTHORIZE</button>
                                        <button onClick={() => rejectEvent(event.original_telemetry.truck.truck_id)} className="flex-1 border-2 border-slate-600 hover:border-slate-500 hover:bg-slate-700 text-slate-300 py-2.5 rounded-lg transition-all font-bold">REJECT</button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* AI Reasoning Event Log */}
                <div className="bg-slate-800/40 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-slate-700/50 h-[600px] flex flex-col">
                    <h3 className="text-blue-400 font-bold mb-6 flex items-center text-lg"><Activity className="w-5 h-5 mr-3" /> Agentic Reasoning Stream</h3>
                    <div className="flex-1 overflow-y-auto pr-3 space-y-4 custom-scrollbar">
                        {telemetry.map((log, idx) => (
                            <div key={idx} className="bg-slate-900/80 p-4 rounded-xl border border-slate-700 shadow-sm hover:border-slate-600 transition-colors">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-slate-500 font-mono text-xs font-semibold tracking-wider">{new Date(log.original_telemetry.timestamp).toLocaleTimeString()}</span>
                                    <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-xs font-bold border border-slate-700">{log.original_telemetry.truck.truck_id}</span>
                                </div>
                                <p className="text-slate-200 text-sm italic mb-3 font-medium text-emerald-50/80 border-l-2 border-emerald-500 pl-3 py-1">"{log.ai_analysis.reasoning}"</p>

                                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800">
                                    <div className="flex items-center space-x-2">
                                        <div className={`p-1 rounded ${log.ai_analysis.prediction.includes('Delay') ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                            <Clock className="w-3.5 h-3.5" />
                                        </div>
                                        <span className={`text-xs font-bold ${log.ai_analysis.prediction.includes('Delay') ? 'text-amber-400' : 'text-emerald-400'}`}>{log.ai_analysis.prediction}</span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <div className="p-1 rounded bg-blue-500/20 text-blue-400">
                                            <MapPin className="w-3.5 h-3.5" />
                                        </div>
                                        <span className="text-xs text-slate-300 font-medium truncate" title={log.original_telemetry.truck.destination}>{log.original_telemetry.truck.destination}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {telemetry.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-70">
                                <Activity className="w-12 h-12 mb-4 animate-pulse text-blue-400/50" />
                                <p className="font-medium">Awaiting Telemetry Stream...</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
