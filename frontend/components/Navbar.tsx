"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className="navbar"
      style={{
        borderBottomColor: scrolled ? "rgba(59,130,246,0.2)" : "rgba(59,130,246,0.10)",
        boxShadow: scrolled ? "0 4px 32px rgba(0,0,0,0.5)" : "none",
        transition: "all 0.3s ease",
      }}
    >
      <div className="navbar-inner">
        {/* Logo */}
        <Link href="/" className="nav-logo" style={{ textDecoration: "none" }}>
          <span className="nav-logo-icon anim-heartbeat">🫀</span>
          <span className="nav-logo-text">CardioXAI</span>
        </Link>

      </div>
    </nav>
  );
}
