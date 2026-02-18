import React, { useEffect, useState, CSSProperties } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, ReferenceLine
} from "recharts";

// ── Types ──────────────────────────────────────────────────────────────
type Run = { run_id: string; has_meta: boolean; has_summary: boolean };
type BotStatus = { running: boolean; pid: number | null };
type PerformanceSummary = {
  ts: number; equity: number; cash: number;
  realized_pnl: number; unrealized_pnl: number; fills: number;
  max_drawdown_pct: number; sharpe_like: number;
  sharpe_low: number; sharpe_high: number;
  points_low: number; points_high: number; regime_ok: boolean;
};
type RunMeta = {
  run_id: string; created_at: string; created_at_ts: number;
  pair: { a: string; b: string };
  config: { paper?: any; dependency?: any };
};
type EquityPoint = {
  ts: number; equity: number; cash: number;
  realized_pnl: number; unrealized_pnl: number; fills: number;
};
type Fill = {
  ts: number; token_id: string; side: string;
  price: number; size_usd: number; shares: number; reason: string;
};
type TimeseriesData = {
  equity: EquityPoint[]; market_mid: any[];
  fills: Fill[]; orders: any[];
};

// ── Colors ─────────────────────────────────────────────────────────────
const C = {
  bg:          "#0a0e17",
  panel:       "#111827",
  panelBorder: "#1e293b",
  text:        "#e2e8f0",
  textDim:     "#64748b",
  accent:      "#3b82f6",
  green:       "#22c55e",
  red:         "#ef4444",
  yellow:      "#eab308",
  chartLine:   "#3b82f6",
  chartGrid:   "#1e293b",
};

// ── Utilities ──────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fmtUsd = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });
const fmtPct = (n: number) => `${(n * 100).toFixed(2)}%`;
const fmtTime = (ts: number) => new Date(ts * 1000).toLocaleTimeString();
const fmtDate = (ts: number) => new Date(ts * 1000).toLocaleString();
const truncToken = (id: string) =>
  id && id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-4)}` : id || "N/A";
const pnlColor = (n: number) => (n > 0.001 ? C.green : n < -0.001 ? C.red : C.textDim);

// ── Shared Styles ──────────────────────────────────────────────────────
const panel: CSSProperties = {
  background: C.panel,
  border: `1px solid ${C.panelBorder}`,
  borderRadius: 8,
  padding: 16,
};

const panelTitle: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: 1.5,
  color: C.textDim,
  marginBottom: 12,
  textTransform: "uppercase" as const,
};

// ── Sub-Components ─────────────────────────────────────────────────────

function Header({ botStatus, onToggle }: {
  botStatus: BotStatus; onToggle: () => void;
}) {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "14px 24px", borderBottom: `1px solid ${C.panelBorder}`, background: C.panel,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 6,
          background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 16, fontWeight: 900, color: "#fff",
        }}>P</div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: 0.5 }}>
            POLYMARKET DEPENDENCY LAB
          </div>
          <div style={{ fontSize: 10, color: C.textDim, letterSpacing: 2, marginTop: 1 }}>
            CONTROL TOWER
          </div>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: botStatus.running ? C.green : C.red,
            boxShadow: `0 0 8px ${botStatus.running ? C.green : C.red}`,
            animation: botStatus.running ? "pulse 2s infinite" : "none",
          }} />
          <span style={{
            fontSize: 12, fontWeight: 600,
            color: botStatus.running ? C.green : C.red,
          }}>
            {botStatus.running ? "LIVE" : "OFFLINE"}
          </span>
          {botStatus.pid && (
            <span style={{ fontSize: 10, color: C.textDim }}>PID {botStatus.pid}</span>
          )}
        </div>
        <button onClick={onToggle} style={{
          background: botStatus.running
            ? "linear-gradient(135deg, #dc2626, #ef4444)"
            : "linear-gradient(135deg, #16a34a, #22c55e)",
          color: "#fff", border: "none", borderRadius: 6,
          padding: "8px 20px", cursor: "pointer",
          fontFamily: "inherit", fontWeight: 700, fontSize: 12,
          letterSpacing: 0.5, transition: "opacity 0.2s",
        }}>
          {botStatus.running ? "STOP BOT" : "START BOT"}
        </button>
      </div>
    </div>
  );
}

function MetricCard({ label, value, sub, color }: {
  label: string; value: string; sub?: string; color?: string;
}) {
  return (
    <div style={{ ...panel, textAlign: "center", padding: "14px 8px" }}>
      <div style={{ fontSize: 10, color: C.textDim, letterSpacing: 1, marginBottom: 6, fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, color: color || C.text }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10, color: C.textDim, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function MetricsBar({ summary }: { summary: PerformanceSummary | null }) {
  if (!summary) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, padding: "0 24px", marginTop: 16 }}>
        {[1,2,3,4,5].map(i => (
          <div key={i} style={{ ...panel, textAlign: "center", padding: "14px 8px" }}>
            <div style={{ fontSize: 10, color: C.textDim }}>---</div>
            <div style={{ fontSize: 20, color: C.textDim }}>--</div>
          </div>
        ))}
      </div>
    );
  }
  const totalPnl = summary.realized_pnl + summary.unrealized_pnl;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, padding: "0 24px", marginTop: 16 }}>
      <MetricCard label="EQUITY" value={fmtUsd(summary.equity)} />
      <MetricCard label="TOTAL P&L" value={(totalPnl >= 0 ? "+" : "") + fmtUsd(totalPnl)} color={pnlColor(totalPnl)}
        sub={`Real: ${fmtUsd(summary.realized_pnl)} | Unreal: ${fmtUsd(summary.unrealized_pnl)}`} />
      <MetricCard label="FILLS" value={String(summary.fills)} sub={`${summary.points_low + summary.points_high} data pts`} />
      <MetricCard label="MAX DRAWDOWN" value={fmtPct(summary.max_drawdown_pct)}
        color={summary.max_drawdown_pct > 0.1 ? C.red : summary.max_drawdown_pct > 0.05 ? C.yellow : C.text} />
      <MetricCard label="SHARPE" value={summary.sharpe_like.toFixed(3)}
        color={summary.sharpe_like > 0 ? C.green : summary.sharpe_like < 0 ? C.red : C.text}
        sub={summary.regime_ok ? `Lo: ${summary.sharpe_low.toFixed(2)} | Hi: ${summary.sharpe_high.toFixed(2)}` : "regime building..."} />
    </div>
  );
}

function EquityChart({ data, startingCash }: { data: EquityPoint[]; startingCash: number }) {
  const chartData = data.map((d) => ({
    ...d,
    time: fmtTime(d.ts),
  }));

  return (
    <div style={{ ...panel }}>
      <div style={panelTitle}>EQUITY CURVE</div>
      {chartData.length < 2 ? (
        <div style={{ height: 280, display: "flex", alignItems: "center", justifyContent: "center", color: C.textDim }}>
          Waiting for data...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.chartGrid} />
            <XAxis dataKey="time" tick={{ fill: C.textDim, fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: C.textDim, fontSize: 10 }} domain={["dataMin - 5", "dataMax + 5"]}
              tickFormatter={(v: number) => `$${v.toFixed(0)}`} />
            <Tooltip
              contentStyle={{
                background: C.panel, border: `1px solid ${C.panelBorder}`,
                borderRadius: 6, fontSize: 11, color: C.text,
              }}
              formatter={(value: number, name: string) => [
                `$${value.toFixed(2)}`,
                name === "equity" ? "Equity" : name,
              ]}
            />
            <ReferenceLine y={startingCash} stroke={C.textDim} strokeDasharray="5 5" label="" />
            <Line type="monotone" dataKey="equity" stroke={C.chartLine} dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function FillsTable({ fills }: { fills: Fill[] }) {
  return (
    <div style={{ ...panel, marginTop: 16 }}>
      <div style={panelTitle}>RECENT FILLS</div>
      {fills.length === 0 ? (
        <div style={{ color: C.textDim, fontSize: 12, padding: "20px 0", textAlign: "center" }}>
          No fills recorded — bot is monitoring for dependency triggers
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.panelBorder}` }}>
                {["Time", "Side", "Price", "Size", "Shares", "Reason"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "6px 8px", color: C.textDim, fontWeight: 600, fontSize: 10, letterSpacing: 1 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fills.slice(-20).reverse().map((f, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${C.panelBorder}22` }}>
                  <td style={{ padding: "6px 8px" }}>{fmtTime(f.ts)}</td>
                  <td style={{ padding: "6px 8px", color: f.side?.toUpperCase() === "BUY" ? C.green : C.red, fontWeight: 700 }}>
                    {f.side?.toUpperCase()}
                  </td>
                  <td style={{ padding: "6px 8px" }}>${Number(f.price).toFixed(4)}</td>
                  <td style={{ padding: "6px 8px" }}>{fmtUsd(Number(f.size_usd))}</td>
                  <td style={{ padding: "6px 8px" }}>{Number(f.shares).toFixed(2)}</td>
                  <td style={{ padding: "6px 8px", color: C.textDim }}>{f.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RunHistory({ runs, selectedId, onSelect }: {
  runs: Run[]; selectedId: string | null; onSelect: (id: string) => void;
}) {
  const reversed = [...runs].reverse();
  return (
    <div style={{ ...panel }}>
      <div style={panelTitle}>RUN HISTORY</div>
      <div style={{ maxHeight: 200, overflowY: "auto" }}>
        {reversed.length === 0 ? (
          <div style={{ color: C.textDim, fontSize: 11, textAlign: "center", padding: 12 }}>
            No runs yet
          </div>
        ) : reversed.map(r => {
          const isSelected = r.run_id === selectedId;
          const shortId = r.run_id.replace("paper-", "");
          return (
            <div key={r.run_id} onClick={() => onSelect(r.run_id)}
              style={{
                padding: "8px 10px", cursor: "pointer", borderRadius: 4,
                fontSize: 12, display: "flex", alignItems: "center", justifyContent: "space-between",
                background: isSelected ? `${C.accent}22` : "transparent",
                borderLeft: isSelected ? `3px solid ${C.accent}` : "3px solid transparent",
                marginBottom: 2, transition: "background 0.15s",
              }}>
              <span style={{ fontWeight: isSelected ? 700 : 400 }}>{shortId}</span>
              <span style={{ fontSize: 10 }}>
                {r.has_summary ? <span style={{ color: C.green }}>done</span> : <span style={{ color: C.yellow }}>live</span>}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PairInfo({ meta }: { meta: RunMeta | null }) {
  if (!meta?.pair) return null;
  return (
    <div style={{ ...panel, marginTop: 12 }}>
      <div style={panelTitle}>MARKET PAIR</div>
      <div style={{ fontSize: 11 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ color: C.textDim }}>Token A</span>
          <span style={{ fontFamily: "monospace", color: C.accent }}>{truncToken(meta.pair.a)}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: C.textDim }}>Token B</span>
          <span style={{ fontFamily: "monospace", color: C.accent }}>{truncToken(meta.pair.b)}</span>
        </div>
      </div>
    </div>
  );
}

function ConfigPanel({ meta, summary }: { meta: RunMeta | null; summary: PerformanceSummary | null }) {
  if (!meta?.config) return null;
  const dep = meta.config.dependency || {};
  const pap = meta.config.paper || {};
  const lat = pap.latency || {};
  const micro = pap.micro || {};

  const items: [string, string][] = [
    ["Starting Cash", fmtUsd(pap.starting_cash_usd || 1000)],
    ["Beta", String(dep.linear?.beta ?? "1.0")],
    ["Trigger Move", fmtPct(dep.trigger_move_pct || 0.03)],
    ["Min Gap", fmtPct(dep.min_gap_pct || 0.02)],
    ["Latency", `${lat.base_ms || 150}ms`],
    ["Region", micro.region || "us-central"],
    ["Slippage", `${pap.slippage_bps || 5} bps`],
  ];

  return (
    <div style={{ ...panel, marginTop: 12 }}>
      <div style={{ ...panelTitle, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>CONFIG</span>
        {summary && (
          <span style={{
            fontSize: 9, padding: "2px 6px", borderRadius: 3,
            background: summary.regime_ok ? `${C.green}22` : `${C.yellow}22`,
            color: summary.regime_ok ? C.green : C.yellow,
          }}>
            {summary.regime_ok ? "REGIME OK" : "BUILDING"}
          </span>
        )}
      </div>
      <div style={{ fontSize: 11 }}>
        {items.map(([k, v]) => (
          <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ color: C.textDim }}>{k}</span>
            <span>{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────
export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [botStatus, setBotStatus] = useState<BotStatus>({ running: false, pid: null });
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);
  const [meta, setMeta] = useState<RunMeta | null>(null);
  const [timeseries, setTimeseries] = useState<TimeseriesData | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => setIsMounted(true), []);

  // Poll runs + status
  useEffect(() => {
    const poll = async () => {
      try {
        const [runsRes, statusRes] = await Promise.all([
          fetch(`${API}/api/runs`), fetch(`${API}/api/control/status`),
        ]);
        const runsData = await runsRes.json();
        const statusData = await statusRes.json();
        setRuns(runsData.runs || []);
        setBotStatus(statusData);
        if (!selectedRunId && runsData.runs?.length > 0) {
          setSelectedRunId(runsData.runs[runsData.runs.length - 1].run_id);
        }
      } catch {}
    };
    poll();
    const t = setInterval(poll, 5000);
    return () => clearInterval(t);
  }, [selectedRunId]);

  // Poll selected run detail
  useEffect(() => {
    if (!selectedRunId) return;
    const poll = async () => {
      try {
        const [detailRes, tsRes] = await Promise.all([
          fetch(`${API}/api/runs/${selectedRunId}`),
          fetch(`${API}/api/runs/${selectedRunId}/timeseries`),
        ]);
        const detail = await detailRes.json();
        const ts = await tsRes.json();
        setSummary(detail.summary || null);
        setMeta(detail.meta || null);
        setTimeseries(ts);
      } catch {}
    };
    poll();
    const t = setInterval(poll, 5000);
    return () => clearInterval(t);
  }, [selectedRunId]);

  const handleToggle = async () => {
    try {
      const endpoint = botStatus.running ? "stop" : "start";
      await fetch(`${API}/api/control/${endpoint}`, { method: "POST" });
      const statusRes = await fetch(`${API}/api/control/status`);
      setBotStatus(await statusRes.json());
    } catch {}
  };

  const startingCash = meta?.config?.paper?.starting_cash_usd || 1000;

  return (
    <div style={{
      background: C.bg, color: C.text, minHeight: "100vh",
      fontFamily: "'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace", fontSize: 13,
    }}>
      <style jsx global>{`
        html, body, #__next { margin: 0; padding: 0; background: ${C.bg}; color: ${C.text}; }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: ${C.bg}; }
        ::-webkit-scrollbar-thumb { background: ${C.panelBorder}; border-radius: 3px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        button:hover { opacity: 0.85; }
      `}</style>

      <Header botStatus={botStatus} onToggle={handleToggle} />
      <MetricsBar summary={summary} />

      <div style={{ display: "flex", gap: 16, padding: "16px 24px", alignItems: "flex-start" }}>
        {/* Left Column */}
        <div style={{ flex: 7, minWidth: 0 }}>
          {isMounted && (
            <EquityChart data={timeseries?.equity || []} startingCash={startingCash} />
          )}
          <FillsTable fills={timeseries?.fills || []} />
        </div>

        {/* Right Column */}
        <div style={{ flex: 3, minWidth: 240 }}>
          <RunHistory runs={runs} selectedId={selectedRunId} onSelect={setSelectedRunId} />
          <PairInfo meta={meta} />
          <ConfigPanel meta={meta} summary={summary} />
        </div>
      </div>
    </div>
  );
}
