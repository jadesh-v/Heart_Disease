// types.ts – shared type definitions for the Heart Disease XAI project

export interface PredictRequest {
  age: number;
  sex: number;
  cp: number;
  trestbps: number;
  chol: number;
  fbs: number;
  restecg: number;
  thalach: number;
  exang: number;
  oldpeak: number;
  slope: number;
  ca: number;
  thal: number;
}

export interface SHAPFeature {
  feature: string;
  value: number;
  shap_value: number;
  direction: "increases" | "decreases";
}

export interface PredictResponse {
  prediction: number;          // 0 or 1
  probability: number;         // percentage 0–100
  risk_level: string;          // "High Risk" | "Moderate Risk" | "Low Risk"
  shap_values: SHAPFeature[];
  top_features: string[];
}

export interface FormValues {
  age: string;
  sex: string;
  cp: string;
  trestbps: string;
  chol: string;
  fbs: string;
  restecg: string;
  thalach: string;
  exang: string;
  oldpeak: string;
  slope: string;
  ca: string;
  thal: string;
}

export type RiskLevel = "High Risk" | "Moderate Risk" | "Low Risk";
