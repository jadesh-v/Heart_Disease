import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "CardioXAI — Explainable AI Heart Disease Prediction",
  description:
    "AI-powered cardiovascular risk assessment using Random Forest + SHAP explainability. Predict heart disease risk from 13 clinical parameters with full transparency.",
  keywords: ["heart disease prediction", "explainable AI", "SHAP", "random forest", "cardiovascular risk", "XAI", "medical AI"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="page-bg">
        <Navbar />
        <div style={{ paddingTop: "68px" }}>{children}</div>
      </body>
    </html>
  );
}
