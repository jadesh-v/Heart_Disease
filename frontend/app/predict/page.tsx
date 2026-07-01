"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import PredictionForm from "@/components/PredictionForm";
import ResultPanel from "@/components/ResultPanel";
import { FormValues, PredictRequest, PredictResponse } from "@/components/types";

const EMPTY_FORM: FormValues = {
  age: "", sex: "", cp: "", trestbps: "", chol: "",
  fbs: "", restecg: "", thalach: "", exang: "",
  oldpeak: "", slope: "", ca: "", thal: "",
};

export default function PredictPage() {
  const [values, setValues] = useState<FormValues>(EMPTY_FORM);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_name");
    router.push("/login");
  };

  const handleChange = (field: keyof FormValues, value: string) => {
    setValues(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload: PredictRequest = {
        age:      Number(values.age),
        sex:      Number(values.sex),
        cp:       Number(values.cp),
        trestbps: Number(values.trestbps),
        chol:     Number(values.chol),
        fbs:      Number(values.fbs),
        restecg:  Number(values.restecg),
        thalach:  Number(values.thalach),
        exang:    Number(values.exang),
        oldpeak:  Number(values.oldpeak),
        slope:    Number(values.slope),
        ca:       Number(values.ca),
        thal:     Number(values.thal),
      };

      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Server error ${res.status}`);
      }

      const data: PredictResponse = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setValues(EMPTY_FORM);
    setError(null);
  };

  return (
    <main style={{ minHeight: "calc(100vh - 68px)", padding: "40px 24px 64px" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>

        {/* Page header */}
        <div style={{ marginBottom: 36, textAlign: "center", position: "relative" }}>
          <button 
            onClick={handleLogout}
            style={{ position: "absolute", right: 0, top: 0, padding: "8px 16px", borderRadius: 8, background: "rgba(255,255,255,0.1)", color: "white", fontSize: 13, fontWeight: 600 }}>
            Log Out
          </button>
          <h1 style={{
            fontSize: "clamp(26px, 4vw, 40px)",
            fontWeight: 900, letterSpacing: "-0.03em", lineHeight: 1.1, marginBottom: 10,
          }}>
            <span className="gradient-blue">Predict</span>{" "}
            <span style={{ color: "var(--text-200)" }}>Heart Disease Risk</span>
          </h1>
        </div>

        {/* Error banner */}
        {error && (
          <div style={{
            marginBottom: 24, padding: "14px 20px", borderRadius: 12,
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)",
            color: "var(--red-400)", fontSize: 13, fontWeight: 600,
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <span style={{ fontSize: 18 }}>⚠️</span>
            {error}
          </div>
        )}

        {/* Two-column layout */}
        <div style={{
          display: "grid",
          gridTemplateColumns: result ? "1fr 380px" : "1fr",
          gap: 28,
          alignItems: "start",
          transition: "grid-template-columns 0.3s ease",
        }}>

          {/* Left – form */}
          <div className="glass" style={{ padding: "32px 28px" }}>
            <PredictionForm
              values={values}
              onChange={handleChange}
              onSubmit={handleSubmit}
              loading={loading}
            />
          </div>

          {/* Right – result */}
          {result && (
            <div style={{ position: "sticky", top: 88 }}>
              <ResultPanel result={result} onReset={handleReset} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
