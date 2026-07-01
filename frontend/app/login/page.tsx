"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  
  // Tabs: 'login' | 'signup'
  const [tab, setTab] = useState<"login" | "signup">("login");
  
  // Login State
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Signup State
  const [signupStep, setSignupStep] = useState<1 | 2 | 3>(1); // 1: Info, 2: OTP, 3: Password
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }

      // Save fake token
      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("user_name", data.user.name);
      
      router.push("/predict");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await fetch("/api/auth/request-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: signupName, email: signupEmail }),
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to request OTP");
      }

      setMessage(data.message);
      setSignupStep(2);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: signupEmail, otp: otp }),
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to verify OTP");
      }

      setMessage(data.message);
      setSignupStep(3);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (signupPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: signupName, email: signupEmail, password: signupPassword }),
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Signup failed");
      }

      setMessage("Signup successful! Please log in.");
      setTab("login");
      setSignupStep(1);
      setSignupName("");
      setSignupEmail("");
      setOtp("");
      setSignupPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: "calc(100vh - 68px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "40px 24px" }}>
      <div className="glass" style={{ width: "100%", maxWidth: 440, padding: "32px", borderRadius: 16 }}>
        
        {/* TABS */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          <button 
            onClick={() => { setTab("login"); setError(null); setMessage(null); }}
            style={{ 
              flex: 1, padding: "10px", borderRadius: 8, fontWeight: 600,
              background: tab === "login" ? "rgba(59,130,246,0.15)" : "transparent",
              color: tab === "login" ? "var(--blue-400)" : "var(--text-300)"
            }}>
            Log In
          </button>
          <button 
            onClick={() => { setTab("signup"); setError(null); setMessage(null); }}
            style={{ 
              flex: 1, padding: "10px", borderRadius: 8, fontWeight: 600,
              background: tab === "signup" ? "rgba(59,130,246,0.15)" : "transparent",
              color: tab === "signup" ? "var(--blue-400)" : "var(--text-300)"
            }}>
            Sign Up
          </button>
        </div>

        {/* ALERTS */}
        {error && (
          <div style={{ padding: "12px", background: "rgba(239,68,68,0.1)", color: "var(--red-400)", borderRadius: 8, marginBottom: 20, fontSize: 14 }}>
            {error}
          </div>
        )}
        {message && (
          <div style={{ padding: "12px", background: "rgba(34,197,94,0.1)", color: "#4ade80", borderRadius: 8, marginBottom: 20, fontSize: 14 }}>
            {message}
          </div>
        )}

        {/* LOGIN FORM */}
        {tab === "login" && (
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Email Address</label>
              <input 
                type="email" required
                value={loginEmail} onChange={e => setLoginEmail(e.target.value)}
                style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Password</label>
              <input 
                type="password" required
                value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
              />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: "100%", padding: "14px", marginTop: 8 }}>
              {loading ? "Logging in..." : "Log In"}
            </button>
          </form>
        )}

        {/* SIGNUP FORM */}
        {tab === "signup" && (
          <div>
            {signupStep === 1 && (
              <form onSubmit={handleRequestOtp} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Full Name</label>
                  <input 
                    type="text" required
                    value={signupName} onChange={e => setSignupName(e.target.value)}
                    style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Email Address</label>
                  <input 
                    type="email" required
                    value={signupEmail} onChange={e => setSignupEmail(e.target.value)}
                    style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
                  />
                </div>
                <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: "100%", padding: "14px", marginTop: 8 }}>
                  {loading ? "Sending OTP..." : "Continue"}
                </button>
              </form>
            )}

            {signupStep === 2 && (
              <form onSubmit={handleVerifyOtp} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Enter OTP sent to {signupEmail}</label>
                  <input 
                    type="text" required
                    value={otp} onChange={e => setOtp(e.target.value)}
                    placeholder="123456"
                    style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white", letterSpacing: "4px", textAlign: "center", fontSize: 20 }}
                  />
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <button type="button" onClick={() => setSignupStep(1)} style={{ flex: 1, padding: "14px", borderRadius: 8, background: "rgba(255,255,255,0.1)", color: "white" }}>
                    Back
                  </button>
                  <button type="submit" disabled={loading} className="btn btn-primary" style={{ flex: 2, padding: "14px" }}>
                    {loading ? "Verifying..." : "Verify OTP"}
                  </button>
                </div>
              </form>
            )}

            {signupStep === 3 && (
              <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Create Password</label>
                  <input 
                    type="password" required minLength={6}
                    value={signupPassword} onChange={e => setSignupPassword(e.target.value)}
                    style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "var(--text-300)" }}>Confirm Password</label>
                  <input 
                    type="password" required minLength={6}
                    value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                    style={{ width: "100%", padding: "12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "white" }}
                  />
                </div>
                <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: "100%", padding: "14px", marginTop: 8 }}>
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
