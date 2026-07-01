import Link from "next/link";

export default function LandingPage() {
  return (
    <main style={{ minHeight: "calc(100vh - 68px)", display: "flex", flexDirection: "column" }}>

      {/* ── HERO ── */}
      <section style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 24px",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Subtle background glow */}
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          background: "radial-gradient(ellipse 70% 55% at 50% 40%, rgba(59,130,246,0.09) 0%, transparent 70%)",
        }} />
        {/* Grid lines */}
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          backgroundImage: "linear-gradient(rgba(59,130,246,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.035) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          maskImage: "radial-gradient(ellipse 75% 65% at 50% 40%, black, transparent)",
          WebkitMaskImage: "radial-gradient(ellipse 75% 65% at 50% 40%, black, transparent)",
        }} />

        <div style={{ position: "relative", textAlign: "center", maxWidth: 720, margin: "0 auto" }}>

          {/* Heading */}
          <h1 style={{
            fontSize: "clamp(40px, 7vw, 76px)",
            fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1.05, marginBottom: 44,
          }}>
            Heart Disease
            <br />
            <span className="gradient-blue">Prediction</span>{" "}
            <span style={{ color: "var(--text-300)", fontWeight: 700 }}>with XAI</span>
          </h1>

          {/* CTA */}
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/login" className="btn btn-primary" style={{ fontSize: 15, padding: "13px 30px" }}>
              <span>🔐</span> Login / Sign Up
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
