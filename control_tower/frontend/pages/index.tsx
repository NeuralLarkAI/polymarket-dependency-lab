import React, { useEffect, useState } from "react";
type Run = { run_id: string; has_meta: boolean; has_summary: boolean };

export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [status, setStatus] = useState<string>("");

  async function loadRuns() {
    const res = await fetch("http://localhost:8000/api/runs");
    const data = await res.json();
    setRuns(data.runs || []);
  }

  async function start() {
    setStatus("starting...");
    const res = await fetch("http://localhost:8000/api/control/start", { method: "POST" });
    setStatus(JSON.stringify(await res.json(), null, 2));
    await loadRuns();
  }
  async function stop() {
    setStatus("stopping...");
    const res = await fetch("http://localhost:8000/api/control/stop", { method: "POST" });
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
      <h1>Control Tower</h1>
      <p>MVP: start/stop bot and inspect runs.</p>

      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <button onClick={start}>Start Bot</button>
        <button onClick={stop}>Stop Bot</button>
      </div>

      <pre style={{ background: "#f4f4f4", padding: 12, whiteSpace: "pre-wrap" }}>{status}</pre>

      <h2>Runs</h2>
      <ul>
        {runs.map((r) => (
          <li key={r.run_id}>
            <a href={`/runs/${r.run_id}`}>{r.run_id}</a> {r.has_summary ? "✅" : "—"}
          </li>
        ))}
      </ul>
    </div>
  );
}
