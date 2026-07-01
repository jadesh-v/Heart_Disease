"use client";

import React from "react";
import { PredictResponse } from "./types";

const FEATURE_LABELS: Record<string, string> = {
  age: "Age", sex: "Sex", cp: "Chest Pain Type", trestbps: "Resting BP",
  chol: "Cholesterol", fbs: "Fasting Blood Sugar", restecg: "Resting ECG",
  thalach: "Max Heart Rate", exang: "Exercise Angina", oldpeak: "ST Depression",
  slope: "ST Slope", ca: "Major Vessels", thal: "Thalassemia",
};

interface Props {
  result: PredictResponse;
  onReset: () => void;
}

export default function ResultPanel({ result, onReset }: Props) {
  const isHigh = result.risk_level === "High Risk";
  const isMod  = result.risk_level === "Moderate Risk";

  const riskClass = isHigh ? "risk-high" : isMod ? "risk-mod" : "risk-low";
  const riskBgClass = isHigh ? "risk-high-bg" : isMod ? "risk-mod-bg" : "risk-low-bg";
  const riskColor = isHigh ? "var(--red-400)" : isMod ? "var(--amber-400)" : "var(--green-400)";
  const riskGlow = isHigh ? "rgba(239,68,68,0.15)" : isMod ? "rgba(251,191,36,0.15)" : "rgba(34,197,94,0.15)";
  const riskEmoji = isHigh ? "⚠️" : isMod ? "🔶" : "✅";

  const maxShap = Math.max(...result.shap_values.map(s => Math.abs(s.shap_value)));
  const sorted = [...result.shap_values].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }} className="anim-fade-up">

      {/* ── Hero result card ──────────────────────────────── */}
      <div
        className="glass"
        style={{
          padding: "28px 24px",
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
          border: `1px solid ${riskColor}30`,
        }}
      >
        {/* bg glow */}
        <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse at center, ${riskGlow} 0%, transparent 70%)`, pointerEvents: "none" }} />

        <div style={{ position: "relative" }}>
          <div style={{ fontSize: 44, marginBottom: 10 }} className="anim-heartbeat">
            {result.prediction === 1 ? "❤️‍🔥" : "💚"}
          </div>

          <h2 style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 10, color: riskColor }}>
            {result.prediction === 1 ? "Heart Disease Detected" : "No Heart Disease Detected"}
          </h2>

          {/* Risk badge */}
          <div style={{ display: "inline-flex", alignItems: "center", gap: 7, padding: "7px 18px", borderRadius: 99, marginBottom: 20 }}
               className={riskBgClass}>
            <span style={{ fontSize: 13 }}>{riskEmoji}</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: riskColor }}>{result.risk_level}</span>
          </div>

          {/* Probability ring */}
          <ProbRing probability={result.probability} color={riskColor} />

          <p style={{ fontSize: 11, color: "var(--text-400)", marginTop: 8, letterSpacing: "0.04em" }}>
            DISEASE PROBABILITY SCORE
          </p>
        </div>
      </div>

      {/* ── Quick stats row ───────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[
          { label: "Prediction", value: result.prediction === 1 ? "Positive" : "Negative", color: riskColor },
          { label: "Risk Level",  value: result.risk_level, color: riskColor },
        ].map(s => (
          <div key={s.label} className="glass-sm" style={{ padding: "14px 16px" }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: "var(--text-400)", marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 15, fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Top 5 features ───────────────────────────────── */}
      <div className="glass-sm" style={{ padding: "20px 20px" }}>
        <div className="section-label" style={{ marginBottom: 14 }}>
          <span>🏆</span><span>Top Influencing Features</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {result.top_features.map((feat, i) => {
            const sv = result.shap_values.find(s => s.feature === feat);
            const pos = sv ? sv.shap_value > 0 : false;
            return (
              <span
                key={feat}
                className="feat-chip"
                style={{
                  background: pos ? "rgba(239,68,68,0.1)" : "rgba(34,197,94,0.1)",
                  border: `1px solid ${pos ? "rgba(239,68,68,0.3)" : "rgba(34,197,94,0.3)"}`,
                  color: pos ? "var(--red-400)" : "var(--green-400)",
                }}
              >
                <span style={{ fontSize: 10, opacity: 0.7, fontWeight: 700 }}>#{i + 1}</span>
                {FEATURE_LABELS[feat] ?? feat}
                <span style={{ fontSize: 11 }}>{pos ? "↑" : "↓"}</span>
              </span>
            );
          })}
        </div>
      </div>

      {/* ── SHAP table ────────────────────────────────────── */}
      <div className="glass-sm" style={{ padding: "20px 20px" }}>
        <div className="section-label" style={{ marginBottom: 6 }}>
          <span>🧬</span><span>SHAP Feature Contributions</span>
        </div>
        <p style={{ fontSize: 12, color: "var(--text-400)", marginBottom: 16, lineHeight: 1.6 }}>
          <span style={{ color: "var(--red-400)" }}>Red ↑</span> features increase heart disease risk.&nbsp;
          <span style={{ color: "var(--green-400)" }}>Green ↓</span> features decrease it.
        </p>

        {/* Table header */}
        <div className="shap-row" style={{ paddingTop: 0, borderBottom: "1px solid var(--border-2)" }}>
          {["Feature", "Value", "SHAP Impact", "Direction"].map(h => (
            <div key={h} style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-400)" }}>{h}</div>
          ))}
        </div>

        {sorted.map(item => {
          const pos = item.shap_value > 0;
          const barW = maxShap > 0 ? (Math.abs(item.shap_value) / maxShap) * 100 : 0;
          return (
            <div key={item.feature} className="shap-row">
              <div style={{ fontSize: 13, fontWeight: 600 }}>{FEATURE_LABELS[item.feature] ?? item.feature}</div>
              <div style={{ fontSize: 12, color: "var(--text-300)", fontFamily: "monospace" }}>{item.value}</div>
              <div>
                <div className="shap-track" style={{ marginBottom: 4 }}>
                  <div className={pos ? "shap-pos" : "shap-neg"} style={{ width: `${barW}%`, transition: "width 0.9s cubic-bezier(.4,0,.2,1)" }} />
                </div>
                <span style={{ fontSize: 10.5, fontFamily: "monospace", color: pos ? "var(--red-400)" : "var(--green-400)" }}>
                  {pos ? "+" : ""}{item.shap_value.toFixed(4)}
                </span>
              </div>
              <div>
                <span
                  style={{
                    fontSize: 10.5, fontWeight: 700, padding: "3px 9px", borderRadius: 99,
                    background: pos ? "rgba(239,68,68,0.12)" : "rgba(34,197,94,0.12)",
                    color: pos ? "var(--red-400)" : "var(--green-400)",
                    border: `1px solid ${pos ? "rgba(239,68,68,0.25)" : "rgba(34,197,94,0.25)"}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  {pos ? "↑ Risk" : "↓ Risk"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reset button */}
      <button onClick={onReset} className="btn btn-outline btn-sm" style={{ width: "100%" }}>
        ↺ &nbsp;Start New Prediction
      </button>
    </div>
  );
}

/* ── Probability Ring ─────────────────────────────────────────── */
function ProbRing({ probability, color }: { probability: number; color: string }) {
  const r = 50;
  const circ = 2 * Math.PI * r;
  const offset = circ - (probability / 100) * circ;
  return (
    <div style={{ display: "flex", justifyContent: "center", margin: "8px 0" }}>
      <div style={{ position: "relative", width: 130, height: 130 }}>
        <svg width="130" height="130" viewBox="0 0 130 130">
          <circle cx="65" cy="65" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
          <circle
            cx="65" cy="65" r={r} fill="none"
            stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={offset}
            transform="rotate(-90 65 65)"
            style={{ transition: "stroke-dashoffset 1.2s ease", filter: `drop-shadow(0 0 8px ${color}70)` }}
          />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: 24, fontWeight: 900, color, lineHeight: 1 }}>{probability.toFixed(1)}%</span>
          <span style={{ fontSize: 9, color: "var(--text-400)", letterSpacing: "0.04em", marginTop: 3 }}>PROBABILITY</span>
        </div>
      </div>
    </div>
  );
}
