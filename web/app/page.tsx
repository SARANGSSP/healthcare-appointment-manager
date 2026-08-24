"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { VitalsLine } from "../components/ui/VitalsLine";
import { Badge } from "../components/ui/Badge";

export default function Home() {
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "unreachable" | "unset">("checking");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) {
      setApiStatus("unset");
      return;
    }
    fetch(`${apiUrl}/api/v1/health`)
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status === "ok" ? "connected" : "unreachable"))
      .catch(() => setApiStatus("unreachable"));
  }, []);

  return (
    <main className="page app-main-narrow" style={{ display: "flex", flexDirection: "column", gap: "2rem", minHeight: "100vh", justifyContent: "center" }}>
      <div style={{ textAlign: "center" }}>
        <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>Healthcare Appointment Manager</h1>
        <p style={{ color: "var(--color-muted)", fontSize: "1.1rem" }}>
          Unified portal for Patients, Doctors, and Administrators
        </p>
      </div>

      <VitalsLine tone="ink" />

      <Card style={{ display: "flex", flexDirection: "column", gap: "1.5rem", padding: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
          <h2 style={{ margin: 0, fontSize: "1.25rem" }}>System Status</h2>
          {apiStatus === "checking" && <Badge tone="amber">Checking Status</Badge>}
          {apiStatus === "connected" && <Badge tone="sage">API Connected</Badge>}
          {apiStatus === "unreachable" && <Badge tone="coral">API Unreachable</Badge>}
          {apiStatus === "unset" && <Badge tone="amber">API Not Configured</Badge>}
        </div>

        {apiStatus === "unset" && (
          <p style={{ fontSize: "0.875rem", color: "var(--color-muted)", margin: 0 }}>
            To enable full connectivity, define <code>NEXT_PUBLIC_API_URL=http://localhost:5000</code> in your local environment settings.
          </p>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <Link href="/login" passHref style={{ textDecoration: "none" }}>
            <Button variant="primary" style={{ width: "100%", height: "100%" }}>
              Log in to Portal
            </Button>
          </Link>
          <Link href="/register" passHref style={{ textDecoration: "none" }}>
            <Button variant="secondary" style={{ width: "100%", height: "100%" }}>
              Register Account
            </Button>
          </Link>
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem" }}>
        <Card style={{ padding: "1.25rem" }}>
          <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Patient Portal</h3>
          <p style={{ fontSize: "0.875rem", color: "var(--color-muted)", margin: 0 }}>
            Search doctors, reserve consultation slots, view details, and receive friendly medication instructions.
          </p>
        </Card>

        <Card style={{ padding: "1.25rem" }}>
          <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Doctor Portal</h3>
          <p style={{ fontSize: "0.875rem", color: "var(--color-muted)", margin: 0 }}>
            Manage daily schedule, review symptom summary cards, and write patient-friendly clinical summaries.
          </p>
        </Card>
      </div>
    </main>
  );
}
