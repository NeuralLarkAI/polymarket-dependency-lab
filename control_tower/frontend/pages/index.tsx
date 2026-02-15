import React, { useEffect, useState } from "react";
type Run = { run_id: string; has_meta: boolean; has_summary: boolean };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [status, setStatus] = useState<string>("");

  async function loadRuns() {
    const res = await fetch(`${API_URL}/api/runs`);
    const data = await res.json();
    setRuns(data.runs || []);
  }

  async function start() {
    setStatus("starting...");
    const res = await fetch(`${API_URL}/api/control/start`, { method: "POST" });
    setStatus(JSON.stringify(await res.json(), null, 2));
    await loadRuns();
  }
  async function stop() {
    setStatus("stopping...");
    const res = await fetch(`${API_URL}/api/control/stop`, { method: "POST" });
    setStatus(JSON.stringify(await res.json(), null, 2));
    await loadRuns();
  }

  useEffect(() => {
    loadRuns();
    const t = setInterval(loadRuns, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>🎯 Polymarket Dependency Lab - Control Tower</h1>
      <p>Monitor and control your live Polymarket trading bot.</p>
      <div style={{ fontSize: 12, color: "#666", marginBottom: 16 }}>
        API: {API_URL}
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <button onClick={start} style={{ padding: "8px 16px", cursor: "pointer" }}>
          ▶️ Start Bot
        </button>
        <button onClick={stop} style={{ padding: "8px 16px", cursor: "pointer" }}>
          ⏸️ Stop Bot
        </button>
      </div>

      <pre style={{ background: "#f4f4f4", padding: 12, whiteSpace: "pre-wrap", borderRadius: 4 }}>{status}</pre>

      <h2>📊 Trading Runs</h2>
      {runs.length === 0 ? (
        <p style={{ color: "#666" }}>No runs yet. Start the bot to begin trading!</p>
      ) : (
        <ul>
          {runs.map((r) => (
            <li key={r.run_id}>
              <a href={`/runs/${r.run_id}`}>{r.run_id}</a> {r.has_summary ? "✅" : "⏳"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
