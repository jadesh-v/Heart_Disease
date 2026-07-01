"use client";

import React from "react";
import { FormValues } from "./types";

interface FieldConfig {
  id: keyof FormValues;
  label: string;
  hint: string;
  type: "number" | "select";
  min?: number; max?: number; step?: number;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

const FIELDS: FieldConfig[] = [
  { id: "age",      label: "Age",                    hint: "Years (1–120)",          type: "number",  min: 1,   max: 120,  step: 1,   placeholder: "e.g. 52" },
  { id: "sex",      label: "Sex",                    hint: "Biological sex",          type: "select",  options: [{ value: "1", label: "1 – Male" }, { value: "0", label: "0 – Female" }] },
  { id: "cp",       label: "Chest Pain Type",         hint: "Type of chest pain",      type: "select",  options: [{ value: "3", label: "3 – Typical Angina" }, { value: "2", label: "2 – Atypical Angina" }, { value: "1", label: "1 – Non-Anginal" }, { value: "0", label: "0 – Asymptomatic" }] },
  { id: "trestbps", label: "Resting Blood Pressure",  hint: "mmHg (80–220)",           type: "number",  min: 80,  max: 220,  step: 1,   placeholder: "e.g. 125" },
  { id: "chol",     label: "Serum Cholesterol",        hint: "mg/dl (100–600)",         type: "number",  min: 100, max: 600,  step: 1,   placeholder: "e.g. 212" },
  { id: "fbs",      label: "Fasting Blood Sugar",      hint: "> 120 mg/dl?",            type: "select",  options: [{ value: "0", label: "0 – Below 120 mg/dl" }, { value: "1", label: "1 – Above 120 mg/dl" }] },
  { id: "restecg",  label: "Resting ECG",              hint: "Electrocardiographic",    type: "select",  options: [{ value: "0", label: "0 – Normal" }, { value: "1", label: "1 – ST-T Abnormality" }, { value: "2", label: "2 – LV Hypertrophy" }] },
  { id: "thalach",  label: "Max Heart Rate",           hint: "bpm (60–220)",            type: "number",  min: 60,  max: 220,  step: 1,   placeholder: "e.g. 168" },
  { id: "exang",    label: "Exercise Induced Angina",  hint: "Angina during exercise?", type: "select",  options: [{ value: "0", label: "0 – No" }, { value: "1", label: "1 – Yes" }] },
  { id: "oldpeak",  label: "ST Depression",            hint: "vs. rest (0.0–10.0)",     type: "number",  min: 0,   max: 10,   step: 0.1, placeholder: "e.g. 1.0" },
  { id: "slope",    label: "ST Slope",                 hint: "Peak exercise segment",   type: "select",  options: [{ value: "0", label: "0 – Downsloping" }, { value: "1", label: "1 – Flat" }, { value: "2", label: "2 – Upsloping" }] },
  { id: "ca",       label: "Major Vessels (CA)",       hint: "Fluoroscopy (0–4)",       type: "select",  options: [{ value: "0", label: "0 – Zero" }, { value: "1", label: "1 – One" }, { value: "2", label: "2 – Two" }, { value: "3", label: "3 – Three" }, { value: "4", label: "4 – Four" }] },
  { id: "thal",     label: "Thalassemia",              hint: "Blood disorder status",   type: "select",  options: [{ value: "0", label: "0 – Fixed Defect" }, { value: "1", label: "1 – Normal" }, { value: "2", label: "2 – Reversible Defect" }, { value: "3", label: "3 – No" }] },
];

const SECTIONS = [
  { title: "Demographics & Vitals",  icon: "🧑‍⚕️", fields: FIELDS.slice(0, 5) },
  { title: "Cardiac Test Results",   icon: "❤️",   fields: FIELDS.slice(5, 10) },
  { title: "Advanced Parameters",    icon: "🔬",   fields: FIELDS.slice(10) },
];

interface Props {
  values: FormValues;
  onChange: (field: keyof FormValues, value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
}

export default function PredictionForm({ values, onChange, onSubmit, loading }: Props) {
  return (
    <form onSubmit={onSubmit} noValidate>
      {SECTIONS.map((section, si) => (
        <div key={section.title} style={{ marginBottom: si < SECTIONS.length - 1 ? 36 : 0 }}>
          {/* Section header */}
          <div className="section-label" style={{ marginBottom: 20 }}>
            <span>{section.icon}</span>
            <span>{section.title}</span>
          </div>

          {/* Fields grid */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(195px, 1fr))",
            gap: "18px 20px",
          }}>
            {section.fields.map(field => (
              <div key={field.id}>
                <label className="field-label" htmlFor={field.id}>
                  {field.label}
                  {values[field.id] !== "" && (
                    <span style={{ color: "var(--green-400)", marginLeft: 6, fontSize: 9 }}>✓</span>
                  )}
                </label>

                {field.type === "select" ? (
                  <select
                    id={field.id}
                    className="field-input"
                    value={values[field.id]}
                    onChange={e => onChange(field.id, e.target.value)}
                    required
                  >
                    <option value="" disabled>Select…</option>
                    {field.options!.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    id={field.id}
                    type="number"
                    className="field-input"
                    value={values[field.id]}
                    onChange={e => onChange(field.id, e.target.value)}
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    placeholder={field.placeholder}
                    required
                  />
                )}

                <p className="field-hint">{field.hint}</p>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Submit button */}
      <div style={{ marginTop: 36, display: "flex", justifyContent: "center" }}>
        <button
          id="predict-button"
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: "100%", maxWidth: 420, padding: "16px 32px", fontSize: 15 }}
        >
          {loading ? (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" className="anim-spin">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
              Analyzing Clinical Data…
            </>
          ) : (
            <>
              <span style={{ fontSize: 18 }}>🫀</span>
              Run Heart Disease Prediction
            </>
          )}
        </button>
      </div>
    </form>
  );
}
